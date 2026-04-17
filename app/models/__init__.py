import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class TriggerType(str, enum.Enum):
    api = "api"
    scheduler = "scheduler"


class TaskCreate(BaseModel):
    trigger_type: TriggerType = TriggerType.api
    target_user_id: str
    target_display_name: Optional[str] = None
    message_text: str
    business_type: str = "customer_service"
    idempotency_key: str
    planned_at: Optional[datetime] = None
    payload: Optional[dict] = None


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    target_user_id: str
    target_display_name: Optional[str] = None
    message_text: str
    business_type: str
    idempotency_key: str
    trigger_type: TriggerType
    retry_count: int = 0
    planned_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskQuery(BaseModel):
    status: Optional[TaskStatus] = None
    target_user_id: Optional[str] = None
    business_type: Optional[str] = None
    limit: int = Field(default=20, le=100)
    offset: int = 0
