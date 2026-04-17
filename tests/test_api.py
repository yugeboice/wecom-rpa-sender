"""基础测试"""
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db import init_db, engine
from app.models.task_orm import Base
from main import app


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("app.services.execute_send")
def test_create_task(mock_send):
    from app.rpa import RPAResult
    mock_send.return_value = RPAResult(success=True, message="ok")

    key = uuid.uuid4().hex
    r = client.post("/api/v1/tasks", json={
        "target_user_id": "user_001",
        "message_text": "hello",
        "idempotency_key": key,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "success"
    assert data["target_user_id"] == "user_001"

    # 幂等测试
    r2 = client.post("/api/v1/tasks", json={
        "target_user_id": "user_001",
        "message_text": "hello",
        "idempotency_key": key,
    })
    assert r2.status_code == 201
    assert r2.json()["task_id"] == data["task_id"]


@patch("app.services.execute_send")
def test_get_task(mock_send):
    from app.rpa import RPAResult
    mock_send.return_value = RPAResult(success=True, message="ok")

    key = uuid.uuid4().hex
    r = client.post("/api/v1/tasks", json={
        "target_user_id": "user_002",
        "message_text": "test",
        "idempotency_key": key,
    })
    task_id = r.json()["task_id"]

    r2 = client.get(f"/api/v1/tasks/{task_id}")
    assert r2.status_code == 200
    assert r2.json()["task_id"] == task_id


def test_get_task_not_found():
    r = client.get("/api/v1/tasks/nonexistent")
    assert r.status_code == 404


@patch("app.services.execute_send")
def test_list_tasks(mock_send):
    from app.rpa import RPAResult
    mock_send.return_value = RPAResult(success=True, message="ok")

    for i in range(3):
        client.post("/api/v1/tasks", json={
            "target_user_id": "user_001",
            "message_text": f"msg {i}",
            "idempotency_key": uuid.uuid4().hex,
        })

    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    assert len(r.json()) == 3
