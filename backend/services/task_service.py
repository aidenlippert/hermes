"""
Task Service

Manages orchestration tasks and execution tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.database.models import Task, Execution, TaskStatus

logger = logging.getLogger(__name__)


class TaskService:
    """Task and execution management"""

    @staticmethod
    async def create_task(
        db: AsyncSession,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None
    ) -> Task:
        """
        Create a new orchestration task.

        Args:
            db: Database session
            user_id: User ID
            query: User's request
            conversation_id: Optional conversation ID

        Returns:
            Created Task object
        """
        task = Task(
            user_id=user_id,
            query=query,
            conversation_id=conversation_id,
            status=TaskStatus.PENDING
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"📝 Task created: {task.id}")

        return task

    @staticmethod
    async def update_task_intent(
        db: AsyncSession,
        task_id: str,
        parsed_intent: Dict[str, Any]
    ):
        """Update task with parsed intent"""
        task = await TaskService.get_task(db, task_id)
        if task:
            task.parsed_intent = parsed_intent
            await db.commit()

    @staticmethod
    async def update_task_plan(
        db: AsyncSession,
        task_id: str,
        execution_plan: Dict[str, Any],
        total_steps: int
    ):
        """Update task with execution plan"""
        task = await TaskService.get_task(db, task_id)
        if task:
            task.execution_plan = execution_plan
            task.total_steps = total_steps
            task.status = TaskStatus.IN_PROGRESS
            await db.commit()

    @staticmethod
    async def complete_task(
        db: AsyncSession,
        task_id: str,
        final_output: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Mark task as completed or failed"""
        task = await TaskService.get_task(db, task_id)
        if task:
            task.final_output = final_output
            task.error_message = error_message
            task.status = TaskStatus.COMPLETED if not error_message else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            await db.commit()

            logger.info(f"{'✅' if not error_message else '❌'} Task {task_id[:8]}... {task.status.value}")

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Task]:
        """Get all tasks for a user"""
        stmt = select(Task).where(
            Task.user_id == user_id
        ).order_by(Task.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_execution(
        db: AsyncSession,
        task_id: str,
        agent_id: str,
        agent_name: str,
        step_number: int,
        task_description: str
    ) -> Execution:
        """Create a new execution step"""
        execution = Execution(
            task_id=task_id,
            agent_id=agent_id,
            agent_name=agent_name,
            step_number=step_number,
            task_description=task_description,
            status=TaskStatus.PENDING
        )

        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        return execution

    @staticmethod
    async def start_execution(
        db: AsyncSession,
        execution_id: str
    ):
        """Mark execution as in progress"""
        stmt = select(Execution).where(Execution.id == execution_id)
        result = await db.execute(stmt)
        execution = result.scalar_one_or_none()

        if execution:
            execution.status = TaskStatus.IN_PROGRESS
            await db.commit()

    @staticmethod
    async def complete_execution(
        db: AsyncSession,
        execution_id: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        duration: float = 0.0,
        cost: float = 0.0
    ):
        """Mark execution as completed or failed"""
        stmt = select(Execution).where(Execution.id == execution_id)
        result_exec = await db.execute(stmt)
        execution = result_exec.scalar_one_or_none()

        if execution:
            execution.result = result
            execution.error_message = error_message
            execution.status = TaskStatus.COMPLETED if not error_message else TaskStatus.FAILED
            execution.duration = duration
            execution.cost = cost
            execution.completed_at = datetime.utcnow()

            # Update task stats
            task = await TaskService.get_task(db, execution.task_id)
            if task:
                if execution.status == TaskStatus.COMPLETED:
                    task.completed_steps += 1
                elif execution.status == TaskStatus.FAILED:
                    task.failed_steps += 1

                task.total_duration += duration
                task.total_cost += cost

            await db.commit()
