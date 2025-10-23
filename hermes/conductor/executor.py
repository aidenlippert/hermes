"""
Execution Engine - Runs Multi-Agent Plans

Takes ExecutionPlan and actually executes it:
1. Runs steps in order
2. Handles dependencies
3. Passes results between agents
4. Error handling and retries
5. Real-time progress updates
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import sys
from pathlib import Path

# Import our A2A client
sys.path.append(str(Path(__file__).parent.parent))
from protocols.a2a_client import A2AClient, A2AResponse, TaskStatus
from conductor.planner import ExecutionPlan, ExecutionStep, StepStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a complete plan"""
    plan: ExecutionPlan
    success: bool
    completed_steps: int
    failed_steps: int
    total_duration: float
    final_output: Optional[Any] = None
    error: Optional[str] = None
    step_results: List[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "total_duration": self.total_duration,
            "final_output": self.final_output,
            "error": self.error,
            "steps": [step.to_dict() for step in self.plan.steps]
        }


class Executor:
    """
    Execution Engine - The hands that do the work.

    This is STEP 3 in Hermes orchestration:
    1. Intent Parser (what user wants)
    2. Workflow Planner (how to do it)
    3. Executor (actually do it) ← THIS

    The Executor:
    - Runs steps in dependency order
    - Calls agents via A2A protocol
    - Passes results between steps
    - Handles errors and retries
    - Streams progress updates
    """

    def __init__(
        self,
        a2a_client: Optional[A2AClient] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize executor.

        Args:
            a2a_client: A2A client for talking to agents (creates one if None)
            max_retries: How many times to retry failed steps
            retry_delay: Seconds to wait between retries
        """
        self.a2a_client = a2a_client or A2AClient()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._progress_callbacks: List[Callable] = []

        logger.info("⚡ Executor initialized")

    def on_progress(self, callback: Callable):
        """
        Register a callback for progress updates.

        Callback signature: callback(event: Dict[str, Any])

        Events:
        - {"type": "step_started", "step": 1, "agent": "..."}
        - {"type": "step_completed", "step": 1, "result": "..."}
        - {"type": "step_failed", "step": 1, "error": "..."}
        """
        self._progress_callbacks.append(callback)

    async def _emit_progress(self, event: Dict[str, Any]):
        """Emit progress event to all callbacks"""
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"❌ Progress callback failed: {e}")

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute a complete plan.

        Args:
            plan: The ExecutionPlan to run

        Returns:
            ExecutionResult with outcomes
        """
        logger.info(f"🎬 Starting execution of plan with {len(plan.steps)} steps")

        start_time = datetime.utcnow()
        completed = 0
        failed = 0

        await self._emit_progress({
            "type": "execution_started",
            "total_steps": len(plan.steps),
            "query": plan.original_query
        })

        try:
            # Execute steps in order
            while True:
                # Get next ready step
                next_step = plan.get_next_step()

                if not next_step:
                    # Check if we're done or stuck
                    pending = sum(1 for s in plan.steps if s.status == StepStatus.PENDING)
                    if pending > 0:
                        logger.error(f"❌ {pending} steps stuck (dependency deadlock)")
                        break
                    else:
                        logger.info("✅ All steps completed")
                        break

                # Execute this step
                success = await self._execute_step(plan, next_step)

                if success:
                    completed += 1
                    next_step.status = StepStatus.COMPLETED
                else:
                    failed += 1
                    next_step.status = StepStatus.FAILED

                    # Check if this failure blocks other steps
                    if self._is_critical_step(plan, next_step):
                        logger.error(f"❌ Critical step {next_step.step_number} failed, aborting")
                        break

            # Calculate final result
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Get final output (from last completed step)
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

            await self._emit_progress({
                "type": "execution_completed",
                "success": result.success,
                "duration": duration
            })

            logger.info(f"🏁 Execution finished: {completed} completed, {failed} failed")

            return result

        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")

            await self._emit_progress({
                "type": "execution_failed",
                "error": str(e)
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
        step: ExecutionStep
    ) -> bool:
        """
        Execute a single step.

        Args:
            plan: The full plan (needed for context)
            step: The step to execute

        Returns:
            True if successful
        """
        logger.info(f"▶️ Step {step.step_number}: {step.agent_name}")

        step.status = StepStatus.IN_PROGRESS

        await self._emit_progress({
            "type": "step_started",
            "step": step.step_number,
            "agent": step.agent_name,
            "task": step.task_description
        })

        # Build task description with context from previous steps
        task_description = step.task_description

        # If this step depends on previous step's output, include it
        if step.input_from_step:
            prev_step = plan.steps[step.input_from_step - 1]
            if prev_step.result:
                task_description = f"{task_description}\n\nInput from previous step:\n{prev_step.result}"

        # Try executing with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"   Attempt {attempt}/{self.max_retries}")

                # Call the agent via A2A
                response = await self.a2a_client.send_task(
                    agent_endpoint=step.agent_endpoint,
                    task_description=task_description
                )

                if response.status == TaskStatus.COMPLETED:
                    # Extract result from artifacts
                    if response.artifacts:
                        # Get first artifact's content
                        result = response.artifacts[0].get("content", "")
                        step.result = result

                        logger.info(f"✅ Step {step.step_number} completed")

                        await self._emit_progress({
                            "type": "step_completed",
                            "step": step.step_number,
                            "result": result[:200]  # First 200 chars
                        })

                        return True
                    else:
                        logger.warning(f"⚠️ Step completed but no artifacts")
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
                        await self._emit_progress({
                            "type": "step_failed",
                            "step": step.step_number,
                            "error": error
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
                    await self._emit_progress({
                        "type": "step_failed",
                        "step": step.step_number,
                        "error": error
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


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))

    from hermes.conductor.planner import ExecutionPlan, ExecutionStep

    async def test_executor():
        """Test the executor"""
        print("\n" + "="*60)
        print("🧪 Testing Executor")
        print("="*60)

        # Create a simple test plan
        plan = ExecutionPlan(
            original_query="Write me a Python function",
            steps=[
                ExecutionStep(
                    step_number=1,
                    agent_name="CodeGenerator",
                    agent_endpoint="http://localhost:10001/a2a",
                    task_description="Write a Python function to calculate fibonacci numbers",
                    depends_on=[],
                    input_from_step=None
                )
            ],
            estimated_duration=5.0
        )

        # Create executor with progress callback
        executor = Executor()

        def progress_callback(event):
            print(f"   📡 {event.get('type')}: {event}")

        executor.on_progress(progress_callback)

        # Execute
        print("\n▶️ Executing plan...")
        print("   (Make sure test_agent_code_generator.py is running on port 10001!)")

        result = await executor.execute(plan)

        print(f"\n{'✅' if result.success else '❌'} Execution completed!")
        print(f"   Completed: {result.completed_steps}")
        print(f"   Failed: {result.failed_steps}")
        print(f"   Duration: {result.total_duration:.2f}s")

        if result.final_output:
            print(f"\n📄 Final output:")
            print(result.final_output)

    asyncio.run(test_executor())
