import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    trigger_type = Column(String(20), nullable=False, default="api")
    target_user_id = Column(String(128), nullable=False)
    target_display_name = Column(String(128), nullable=True)
    message_text = Column(Text, nullable=False)
    business_type = Column(String(64), nullable=False, default="customer_service")
    idempotency_key = Column(String(128), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
    planned_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    payload = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
