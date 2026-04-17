"""最小 Demo: 提交一个发送任务"""
import httpx
import uuid
import sys

BASE = "http://127.0.0.1:8000/api/v1"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "user_001"
    message = sys.argv[2] if len(sys.argv) > 2 else "你好，这是一条测试消息"

    resp = httpx.post(
        f"{BASE}/tasks",
        json={
            "target_user_id": target,
            "message_text": message,
            "idempotency_key": uuid.uuid4().hex,
            "business_type": "demo",
        },
    )
    print(f"Status: {resp.status_code}")
    print(resp.json())


if __name__ == "__main__":
    main()
