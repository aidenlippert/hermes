"""
Streaming Executor - Executor with Real-time WebSocket Events

This is an enhanced version of the executor that emits events via WebSocket.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from hermes.protocols.a2a_client import A2AClient, A2AResponse, TaskStatus as A2ATaskStatus
from hermes.conductor.planner import ExecutionPlan, ExecutionStep, StepStatus
from hermes.conductor.executor import ExecutionResult

logger = logging.getLogger(__name__)


class StreamingExecutor:
    """
    Executor with real-time WebSocket event streaming.

    Emits events at every stage:
    - Step started
    - Agent called
    - Agent thinking
    - Step completed
    - Progress updates
    """

    def __init__(
        self,
        a2a_client: Optional[A2AClient] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        event_callback: Optional[Callable] = None
    ):
        """
        Initialize streaming executor.

        Args:
            a2a_client: A2A client for talking to agents
            max_retries: How many times to retry failed steps
            retry_delay: Seconds to wait between retries
            event_callback: Async function to call with events
        """
        self.a2a_client = a2a_client or A2AClient()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.event_callback = event_callback

        logger.info("⚡ Streaming Executor initialized")

    async def _emit_event(self, event: Dict[str, Any]):
        """
        Emit an event via callback.

        Args:
            event: Event data
        """
        if self.event_callback:
            try:
                if asyncio.iscoroutinefunction(self.event_callback):
                    await self.event_callback(event)
                else:
                    self.event_callback(event)
            except Exception as e:
                logger.error(f"❌ Event emission failed: {e}")

    async def execute(self, plan: ExecutionPlan, task_id: str) -> ExecutionResult:
        """
        Execute a complete plan with real-time event streaming.

        Args:
            plan: The ExecutionPlan to run
            task_id: Task ID for event routing

        Returns:
            ExecutionResult with outcomes
        """
        logger.info(f"🎬 Starting streaming execution: {len(plan.steps)} steps")

        # Emit execution started event
        await self._emit_event({
            "type": "execution_started",
            "task_id": task_id,
            "total_steps": len(plan.steps),
            "message": f"⚡ Starting execution: {len(plan.steps)} steps"
        })

        start_time = datetime.utcnow()
        completed = 0
        failed = 0

        try:
            # Execute steps in order
            while True:
                # Get next ready step
                next_step = plan.get_next_step()

                if not next_step:
                    # Check if we're done or stuck
                    pending = sum(1 for s in plan.steps if s.status == StepStatus.PENDING)
                    if pending > 0:
                        logger.error(f"❌ {pending} steps stuck")
                        await self._emit_event({
                            "type": "error",
                            "task_id": task_id,
                            "message": f"❌ {pending} steps stuck (dependency deadlock)"
                        })
                        break
                    else:
                        logger.info("✅ All steps completed")
                        break

                # Execute this step
                success = await self._execute_step(plan, next_step, task_id)

                if success:
                    completed += 1
                    next_step.status = StepStatus.COMPLETED
                else:
                    failed += 1
                    next_step.status = StepStatus.FAILED

                    # Check if this failure blocks other steps
                    if self._is_critical_step(plan, next_step):
                        logger.error(f"❌ Critical step {next_step.step_number} failed")
                        await self._emit_event({
                            "type": "error",
                            "task_id": task_id,
                            "message": f"❌ Critical step {next_step.step_number} failed, aborting"
                        })
                        break

            # Calculate final result
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Get final output
            final_output = None
            for step in reversed(plan.steps):
                if step.status == StepStatus.COMPLETED and step.result:
                    final_output = step.result
                    break

            result = ExecutionResult(
                plan=plan,
                success=failed == 0,
                completed_steps=completed,
                failed_steps=failed,
                total_duration=duration,
                final_output=final_output
            )

            # Emit completion event
            if result.success:
                await self._emit_event({
                    "type": "task_completed",
                    "task_id": task_id,
                    "duration": duration,
                    "result_preview": final_output[:100] if final_output else None,
                    "message": f"✅ Task completed in {duration:.1f}s"
                })
            else:
                await self._emit_event({
                    "type": "task_failed",
                    "task_id": task_id,
                    "error": "One or more steps failed",
                    "message": f"❌ Task failed: {failed} steps failed"
                })

            return result

        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")

            await self._emit_event({
                "type": "task_failed",
                "task_id": task_id,
                "error": str(e),
                "message": f"❌ Execution error: {str(e)}"
            })

            return ExecutionResult(
                plan=plan,
                success=False,
                completed_steps=completed,
                failed_steps=failed,
                total_duration=(datetime.utcnow() - start_time).total_seconds(),
                error=str(e)
            )

    async def _execute_step(
        self,
        plan: ExecutionPlan,
        step: ExecutionStep,
        task_id: str
    ) -> bool:
        """
        Execute a single step with event streaming.

        Args:
            plan: The full plan
            step: The step to execute
            task_id: Task ID

        Returns:
            True if successful
        """
        logger.info(f"▶️ Step {step.step_number}: {step.agent_name}")

        step.status = StepStatus.IN_PROGRESS

        # Emit step started event
        await self._emit_event({
            "type": "step_started",
            "task_id": task_id,
            "step_number": step.step_number,
            "agent_name": step.agent_name,
            "task_description": step.task_description,
            "total_steps": len(plan.steps),
            "progress": step.step_number / len(plan.steps),
            "message": f"▶️ Step {step.step_number}/{len(plan.steps)}: {step.agent_name}"
        })

        # Build task description with context
        task_description = step.task_description

        if step.input_from_step:
            prev_step = plan.steps[step.input_from_step - 1]
            if prev_step.result:
                task_description = f"{task_description}\n\nInput from previous step:\n{prev_step.result}"

        # Try executing with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"   Attempt {attempt}/{self.max_retries}")

                # Emit agent thinking event
                await self._emit_event({
                    "type": "agent_thinking",
                    "task_id": task_id,
                    "agent_name": step.agent_name,
                    "step_number": step.step_number,
                    "message": f"💭 {step.agent_name} is working..."
                })

                # Call the agent via A2A
                response = await self.a2a_client.send_task(
                    agent_endpoint=step.agent_endpoint,
                    task_description=task_description
                )

                if response.status == A2ATaskStatus.COMPLETED:
                    # Extract result
                    if response.artifacts:
                        result = response.artifacts[0].get("content", "")
                        step.result = result

                        logger.info(f"✅ Step {step.step_number} completed")

                        # Emit step completed event
                        await self._emit_event({
                            "type": "step_completed",
                            "task_id": task_id,
                            "step_number": step.step_number,
                            "agent_name": step.agent_name,
                            "result_preview": result[:200] if result else None,
                            "total_steps": len(plan.steps),
                            "progress": step.step_number / len(plan.steps),
                            "message": f"✅ Step {step.step_number}/{len(plan.steps)} completed"
                        })

                        return True

                else:
                    # Task failed
                    error = response.error or f"Status: {response.status}"
                    step.error = error

                    logger.error(f"❌ Step {step.step_number} failed: {error}")

                    if attempt < self.max_retries:
                        logger.info(f"   Retrying in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        # Emit failure event
                        await self._emit_event({
                            "type": "step_failed",
                            "task_id": task_id,
                            "step_number": step.step_number,
                            "agent_name": step.agent_name,
                            "error": error,
                            "message": f"❌ Step {step.step_number} failed: {error[:100]}"
                        })

                        return False

            except Exception as e:
                error = str(e)
                step.error = error

                logger.error(f"❌ Step {step.step_number} error: {error}")

                if attempt < self.max_retries:
                    logger.info(f"   Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    await self._emit_event({
                        "type": "step_failed",
                        "task_id": task_id,
                        "step_number": step.step_number,
                        "agent_name": step.agent_name,
                        "error": error,
                        "message": f"❌ Step {step.step_number} error: {error[:100]}"
                    })

                    return False

        return False

    def _is_critical_step(self, plan: ExecutionPlan, step: ExecutionStep) -> bool:
        """Check if other steps depend on this step"""
        step_num = step.step_number
        for s in plan.steps:
            if step_num in s.depends_on:
                return True
        return False
