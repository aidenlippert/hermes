"""
Workflow execution engine (Sprint 5)

Orchestrates multi-agent workflows with parallel execution, retries,
backoff, cancellation, and real-time event streaming.
"""
import asyncio
import uuid
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models_workflows import WorkflowRun, NodeRun
from backend.services.workflows import compile_workflow, WorkflowValidationError
from backend.websocket.manager import manager as ws_manager
from backend.websocket.events import build_workflow_event
import logging

logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails"""
    pass


class WorkflowRunner:
    """
    Executes compiled workflows with support for:
    - Parallel execution of independent nodes
    - Retries with exponential backoff
    - Cancellation
    - Real-time WebSocket events
    - Context/variable management
    """
    
    def __init__(
        self,
        db: AsyncSession,
        workflow_run_id: str,
        compiled_workflow: Dict[str, Any],
        input_data: Dict[str, Any]
    ):
        self.db = db
        self.workflow_run_id = workflow_run_id
        self.compiled = compiled_workflow
        self.input_data = input_data
        
        self.nodes = compiled_workflow['nodes']
        self.execution_levels = compiled_workflow['execution_levels']
        self.adjacency = compiled_workflow['adjacency']
        
        # Runtime state
        self.context: Dict[str, Any] = {"input": input_data}
        self.node_outputs: Dict[str, Any] = {}
        self.cancelled = False
        self.total_cost = 0.0
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Returns:
            Final workflow output
            
        Raises:
            WorkflowExecutionError if execution fails
        """
        try:
            # Update run status to running
            await self._update_run_status("running", started_at=datetime.utcnow())
            await self._emit_event("workflow_started", {"workflow_run_id": self.workflow_run_id})
            
            # Execute levels in order
            for level_idx, level_nodes in enumerate(self.execution_levels):
                if self.cancelled:
                    await self._handle_cancellation()
                    return {"status": "cancelled"}
                
                await self._emit_event("level_started", {
                    "level": level_idx,
                    "nodes": level_nodes,
                    "total_levels": len(self.execution_levels)
                })
                
                # Execute nodes in this level in parallel
                tasks = [self._execute_node(node_id) for node_id in level_nodes]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for failures
                for node_id, result in zip(level_nodes, results):
                    if isinstance(result, Exception):
                        error_msg = f"Node {node_id} failed: {str(result)}"
                        await self._handle_node_failure(node_id, error_msg)
                        
                        # Check on_error strategy
                        on_error = self.compiled['workflow'].get('on_error', 'fail')
                        if on_error == 'fail':
                            raise WorkflowExecutionError(error_msg)
                        # If 'continue', we keep going
                
                await self._emit_event("level_completed", {
                    "level": level_idx,
                    "nodes_completed": len([r for r in results if not isinstance(r, Exception)]),
                    "nodes_failed": len([r for r in results if isinstance(r, Exception)])
                })
            
            # Workflow completed successfully
            output_data = self._gather_final_output()
            await self._update_run_status(
                "completed",
                completed_at=datetime.utcnow(),
                output_data=output_data,
                total_cost=self.total_cost
            )
            await self._emit_event("workflow_completed", {
                "output": output_data,
                "total_cost": self.total_cost
            })
            
            return output_data
            
        except Exception as e:
            logger.error(f"Workflow {self.workflow_run_id} failed: {e}", exc_info=True)
            await self._update_run_status(
                "failed",
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
            await self._emit_event("workflow_failed", {"error": str(e)})
            raise
    
    async def _execute_node(self, node_id: str) -> Dict[str, Any]:
        """
        Execute a single node with retries.
        
        Returns:
            Node output data
        """
        node = self.nodes[node_id]
        node_type = node['node_type']
        max_retries = node.get('retry_count', 3)
        retry_delay = node.get('retry_delay_seconds', 5)
        
        # Create node run record
        node_run_id = str(uuid.uuid4())
        node_run = NodeRun(
            id=node_run_id,
            workflow_run_id=self.workflow_run_id,
            node_id=node_id,
            status="pending",
            attempt_number=1
        )
        self.db.add(node_run)
        await self.db.commit()
        
        await self._emit_event("node_started", {
            "node_id": node_id,
            "node_type": node_type,
            "node_run_id": node_run_id
        })
        
        # Retry loop
        for attempt in range(1, max_retries + 1):
            try:
                node_run.attempt_number = attempt
                node_run.status = "running"
                node_run.started_at = datetime.utcnow()
                await self.db.commit()
                
                # Resolve input data from context/bindings
                input_data = await self._resolve_node_inputs(node)
                node_run.input_data = json.dumps(input_data)
                await self.db.commit()
                
                # Execute based on node type
                start_time = time.time()
                
                if node_type == "agent_call":
                    output, cost = await self._execute_agent_call(node, input_data)
                elif node_type == "tool_call":
                    output, cost = await self._execute_tool_call(node, input_data)
                elif node_type == "human_gate":
                    output, cost = await self._execute_human_gate(node, input_data)
                elif node_type == "condition":
                    output, cost = await self._execute_condition(node, input_data)
                elif node_type in ("parallel", "join"):
                    # These are structural nodes, no execution needed
                    output, cost = input_data, 0.0
                else:
                    raise WorkflowExecutionError(f"Unknown node type: {node_type}")
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Update node run with success
                node_run.status = "completed"
                node_run.completed_at = datetime.utcnow()
                node_run.output_data = json.dumps(output)
                node_run.cost = cost
                node_run.duration_ms = duration_ms
                await self.db.commit()
                
                # Store output in context
                self.node_outputs[node_id] = output
                self.total_cost += cost or 0.0
                
                await self._emit_event("node_completed", {
                    "node_id": node_id,
                    "node_run_id": node_run_id,
                    "output": output,
                    "cost": cost,
                    "duration_ms": duration_ms
                })
                
                return output
                
            except Exception as e:
                logger.warning(f"Node {node_id} attempt {attempt} failed: {e}")
                
                if attempt < max_retries:
                    # Retry with backoff
                    backoff_delay = retry_delay * (2 ** (attempt - 1))
                    await self._emit_event("node_retry", {
                        "node_id": node_id,
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "retry_in_seconds": backoff_delay,
                        "error": str(e)
                    })
                    await asyncio.sleep(backoff_delay)
                else:
                    # Final failure
                    node_run.status = "failed"
                    node_run.completed_at = datetime.utcnow()
                    node_run.error_message = str(e)
                    await self.db.commit()
                    
                    await self._emit_event("node_failed", {
                        "node_id": node_id,
                        "node_run_id": node_run_id,
                        "error": str(e),
                        "attempts": max_retries
                    })
                    
                    raise
    
    async def _resolve_node_inputs(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve node inputs from context and previous node outputs.
        
        Supports bindings like:
        - "$node_id.output_name" - reference to another node's output
        - "$context.variable_name" - reference to workflow context
        - Literal values
        """
        inputs = node.get('inputs', {})
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
        
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith('$'):
                # This is a reference
                parts = value[1:].split('.', 1)
                if len(parts) == 2:
                    source, field = parts
                    if source == 'context':
                        resolved[key] = self.context.get(field)
                    elif source in self.node_outputs:
                        node_output = self.node_outputs[source]
                        if isinstance(node_output, dict):
                            resolved[key] = node_output.get(field)
                        else:
                            resolved[key] = node_output
                    else:
                        resolved[key] = value  # Keep original if can't resolve
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    async def _execute_agent_call(
        self, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """Execute an agent call node"""
        # TODO: Integrate with existing A2A execution logic
        # For now, mock response
        agent_id = node.get('agent_id')
        action = node.get('action')
        
        await self._emit_event("agent_calling", {
            "agent_id": agent_id,
            "action": action,
            "input": input_data
        })
        
        # Simulate agent call (replace with real A2A call)
        await asyncio.sleep(0.5)
        
        output = {
            "result": f"Agent {agent_id} executed {action}",
            "data": input_data,
            "status": "success"
        }
        cost = 0.05  # Mock cost
        
        return output, cost
    
    async def _execute_tool_call(
        self, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """Execute a tool call node"""
        action = node.get('action')
        
        # Mock tool execution
        output = {
            "tool": action,
            "input": input_data,
            "result": "Tool executed successfully"
        }
        cost = 0.01
        
        return output, cost
    
    async def _execute_human_gate(
        self, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """Execute a human gate (approval) node"""
        # Emit event and wait for approval
        await self._emit_event("human_gate_waiting", {
            "node_id": node['node_id'],
            "prompt": node.get('config', {}).get('prompt', 'Approval required'),
            "input": input_data
        })
        
        # TODO: Implement actual approval waiting mechanism
        # For now, auto-approve after short delay
        await asyncio.sleep(1)
        
        output = {"approved": True, "input": input_data}
        cost = 0.0
        
        return output, cost
    
    async def _execute_condition(
        self, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """Execute a conditional node"""
        config = node.get('config', {})
        if isinstance(config, str):
            config = json.loads(config)
        
        condition = config.get('condition_expression', 'true')
        
        # Simple condition evaluation (can be enhanced with safe eval)
        result = eval(condition, {"__builtins__": {}}, {"input": input_data, "context": self.context})
        
        output = {"condition_result": result, "input": input_data}
        cost = 0.0
        
        return output, cost
    
    async def _update_run_status(
        self,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        total_cost: Optional[float] = None
    ):
        """Update workflow run status in database"""
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == self.workflow_run_id)
        )
        run = result.scalar_one()
        
        run.status = status
        if started_at:
            run.started_at = started_at
        if completed_at:
            run.completed_at = completed_at
        if output_data is not None:
            run.output_data = json.dumps(output_data)
        if error_message:
            run.error_message = error_message
        if total_cost is not None:
            run.total_cost = total_cost
        
        await self.db.commit()
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit WebSocket event for workflow progress"""
        event = build_workflow_event(
            event_type=event_type,
            workflow_run_id=self.workflow_run_id,
            data=data
        )
        await ws_manager.broadcast_to_workflow(self.workflow_run_id, event)
    
    async def _handle_node_failure(self, node_id: str, error: str):
        """Handle node failure based on workflow config"""
        logger.error(f"Node {node_id} in workflow {self.workflow_run_id} failed: {error}")
        # Fallback logic can be added here
    
    async def _handle_cancellation(self):
        """Handle workflow cancellation"""
        await self._update_run_status("cancelled", completed_at=datetime.utcnow())
        await self._emit_event("workflow_cancelled", {"reason": "User requested cancellation"})
    
    def _gather_final_output(self) -> Dict[str, Any]:
        """Gather final output from terminal nodes"""
        # Find nodes with no outgoing edges (terminal nodes)
        terminal_nodes = [
            node_id for node_id in self.nodes.keys()
            if not self.adjacency.get(node_id)
        ]
        
        if len(terminal_nodes) == 1:
            return self.node_outputs.get(terminal_nodes[0], {})
        else:
            # Multiple terminal nodes - return all
            return {
                node_id: self.node_outputs.get(node_id, {})
                for node_id in terminal_nodes
            }
    
    async def cancel(self):
        """Cancel workflow execution"""
        self.cancelled = True
        await self._emit_event("workflow_cancelling", {})


async def execute_workflow(
    db: AsyncSession,
    workflow_run_id: str,
    workflow_dict: Dict[str, Any],
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to compile and execute a workflow.
    
    Args:
        db: Database session
        workflow_run_id: ID of the workflow run
        workflow_dict: Workflow definition
        input_data: Initial input data
        
    Returns:
        Workflow output
        
    Raises:
        WorkflowValidationError: If workflow is invalid
        WorkflowExecutionError: If execution fails
    """
    # Compile workflow
    compiled = compile_workflow(workflow_dict)
    
    # Execute
    runner = WorkflowRunner(db, workflow_run_id, compiled, input_data)
    output = await runner.execute()
    
    return output
