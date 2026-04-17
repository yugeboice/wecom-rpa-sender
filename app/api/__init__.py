import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TaskCreate, TaskQuery, TaskResponse, TaskStatus
from app.repositories import TaskRepository
from app.services import process_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_response(task) -> TaskResponse:
    return TaskResponse(
        task_id=task.task_id,
        status=TaskStatus(task.status),
        target_user_id=task.target_user_id,
        target_display_name=task.target_display_name,
        message_text=task.message_text,
        business_type=task.business_type,
        idempotency_key=task.idempotency_key,
        trigger_type=task.trigger_type,
        retry_count=task.retry_count,
        planned_at=task.planned_at,
        sent_at=task.sent_at,
        failure_reason=task.failure_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    repo = TaskRepository(db)

    # 幂等检查
    existing = repo.get_by_idempotency_key(data.idempotency_key)
    if existing:
        logger.info("Idempotent hit: %s", data.idempotency_key)
        return _task_to_response(existing)

    task = repo.create(data)
    logger.info("Task created: %s", task.task_id)

    # 如果没有 planned_at，立即异步触发（简化版：同步处理）
    if not data.planned_at:
        process_task(task.task_id)
        db.refresh(task)

    return _task_to_response(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task = repo.get_by_task_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[str] = None,
    target_user_id: Optional[str] = None,
    business_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    repo = TaskRepository(db)
    tasks = repo.query_tasks(
        status=status,
        target_user_id=target_user_id,
        business_type=business_type,
        limit=limit,
        offset=offset,
    )
    return [_task_to_response(t) for t in tasks]


@router.post("/{task_id}/retry", response_model=TaskResponse)
def retry_task(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task = repo.get_by_task_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.failed.value:
        raise HTTPException(status_code=400, detail="Only failed tasks can be retried")

    task.retry_count = 0
    task.status = TaskStatus.pending.value
    db.commit()
    db.refresh(task)

    process_task(task.task_id)
    db.refresh(task)
    return _task_to_response(task)
