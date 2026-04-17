import logging

from app.config.settings import settings
from app.db import SessionLocal
from app.models import TaskStatus
from app.repositories import TaskRepository
from app.rpa import RPAResult, execute_send

logger = logging.getLogger(__name__)


def process_task(task_id: str) -> bool:
    """处理单个任务：执行 RPA 发送并更新状态"""
    db = SessionLocal()
    try:
        repo = TaskRepository(db)
        task = repo.get_by_task_id(task_id)
        if not task:
            logger.error("Task %s not found", task_id)
            return False

        if task.status not in (TaskStatus.pending.value, TaskStatus.failed.value):
            logger.info("Task %s status=%s, skip", task_id, task.status)
            return False

        # 标记 running
        repo.update_status(task, TaskStatus.running)
        logger.info("Task %s -> running", task_id)

        # 执行 RPA
        result: RPAResult = execute_send(
            task_id=task.task_id,
            target_user_id=task.target_user_id,
            message_text=task.message_text,
            target_display_name=task.target_display_name,
        )

        if result.success:
            repo.update_status(task, TaskStatus.success)
            logger.info("Task %s -> success", task_id)
            return True
        else:
            repo.increment_retry(task)
            if task.retry_count >= settings.max_retry_count:
                repo.update_status(task, TaskStatus.failed, failure_reason=result.message)
                logger.warning("Task %s -> failed (max retries)", task_id)
            else:
                repo.update_status(task, TaskStatus.failed, failure_reason=result.message)
                logger.info("Task %s -> failed (retry %d/%d)", task_id, task.retry_count, settings.max_retry_count)
            return False
    finally:
        db.close()


def process_pending_tasks():
    """扫描并处理所有待执行任务"""
    db = SessionLocal()
    try:
        repo = TaskRepository(db)
        # 处理 pending 任务
        pending = repo.list_pending(limit=5)
        for task in pending:
            process_task(task.task_id)

        # 处理可重试的 failed 任务
        retryable = repo.list_retryable(settings.max_retry_count)
        for task in retryable:
            process_task(task.task_id)
    finally:
        db.close()
