import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import TaskCreate, TaskStatus
from app.models.task_orm import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_idempotency_key(self, key: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.idempotency_key == key).first()

    def get_by_task_id(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def create(self, data: TaskCreate) -> Task:
        task = Task(
            task_id=uuid.uuid4().hex,
            trigger_type=data.trigger_type.value,
            target_user_id=data.target_user_id,
            target_display_name=data.target_display_name,
            message_text=data.message_text,
            business_type=data.business_type,
            idempotency_key=data.idempotency_key,
            status=TaskStatus.pending.value,
            planned_at=data.planned_at,
            payload=json.dumps(data.payload) if data.payload else None,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_status(
        self, task: Task, status: TaskStatus, failure_reason: Optional[str] = None
    ) -> Task:
        task.status = status.value
        task.updated_at = datetime.utcnow()
        if status == TaskStatus.success:
            task.sent_at = datetime.utcnow()
        if failure_reason:
            task.failure_reason = failure_reason
        self.db.commit()
        self.db.refresh(task)
        return task

    def increment_retry(self, task: Task) -> Task:
        task.retry_count += 1
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_pending(self, limit: int = 10) -> list[Task]:
        now = datetime.utcnow()
        return (
            self.db.query(Task)
            .filter(
                Task.status == TaskStatus.pending.value,
                (Task.planned_at <= now) | (Task.planned_at.is_(None)),
            )
            .order_by(Task.created_at.asc())
            .limit(limit)
            .all()
        )

    def list_retryable(self, max_retry: int) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(
                Task.status == TaskStatus.failed.value,
                Task.retry_count < max_retry,
            )
            .order_by(Task.created_at.asc())
            .all()
        )

    def query_tasks(
        self,
        status: Optional[str] = None,
        target_user_id: Optional[str] = None,
        business_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Task]:
        q = self.db.query(Task)
        if status:
            q = q.filter(Task.status == status)
        if target_user_id:
            q = q.filter(Task.target_user_id == target_user_id)
        if business_type:
            q = q.filter(Task.business_type == business_type)
        return q.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
