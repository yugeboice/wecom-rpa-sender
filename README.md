# 企业微信 RPA 消息发送器

客服 Agent 的企业微信桌面消息发送执行器。通过 macOS 企业微信桌面客户端 RPA 发送消息。

## 架构

```
客服 Agent → REST API → 任务入库 → Scheduler 扫描 → RPA 执行 → 状态回写
```

## 快速开始

```bash
# 1. 初始化
chmod +x scripts/*.sh
./scripts/setup.sh

# 2. 编辑配置
vim .env                           # 修改参数
vim config/user_mapping.json       # 添加 user_id -> 搜索关键字映射

# 3. 启动
./scripts/start.sh

# 4. 测试
python demo.py user_001 "你好"
```

## API

### 创建任务
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": "user_001",
    "message_text": "你好，请问有什么可以帮您？",
    "idempotency_key": "unique-key-123",
    "business_type": "customer_service"
  }'
```

### 查询任务
```bash
curl http://localhost:8000/api/v1/tasks/{task_id}
curl http://localhost:8000/api/v1/tasks?status=success&limit=10
```

### 重试失败任务
```bash
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/retry
```

### 健康检查
```bash
curl http://localhost:8000/health
```

## 定时任务

提交任务时设置 `planned_at` 字段（ISO 时间），Scheduler 会在到期时自动执行：

```json
{
  "target_user_id": "user_001",
  "message_text": "定时提醒",
  "idempotency_key": "scheduled-001",
  "planned_at": "2026-04-18T09:00:00"
}
```

## 任务状态机

```
pending → running → success
                  → failed (retry_count < max → 自动重试回 pending)
                         (retry_count >= max → 终态 failed)
```

## 目录结构

```
├── main.py                 # FastAPI 入口
├── app/
│   ├── api/                # API 路由
│   ├── config/             # 配置 & 用户映射
│   ├── db/                 # 数据库连接
│   ├── models/             # Pydantic 模型 & ORM
│   ├── repositories/       # 数据访问层
│   ├── rpa/                # RPA 执行器（pyautogui）
│   ├── scheduler/          # APScheduler 定时任务
│   └── services/           # 业务逻辑
├── tests/                  # 测试
├── scripts/                # 启动/初始化脚本
├── screenshots/            # RPA 截图
└── data/                   # SQLite 数据库
```

## 已知限制

1. **macOS only** — RPA 层使用 osascript 激活窗口、pbcopy 输入中文，仅支持 macOS
2. **需要辅助功能权限** — pyautogui 需要在 系统偏好设置 → 安全性与隐私 → 辅助功能 中授权终端/Python
3. **单实例** — RPA 操作会占用屏幕焦点，同一时刻只能执行一个发送任务
4. **搜索准确性** — 搜索关键字可能匹配到多个联系人，默认选第一个结果
5. **无发送确认** — 目前无法通过 RPA 验证消息是否真正发送成功（无 OCR），仅判断流程是否无异常
6. **中文输入依赖剪贴板** — 通过 pbcopy + Cmd+V 输入中文，会覆盖用户剪贴板
7. **企业微信版本依赖** — 快捷键（Cmd+F 搜索）可能因版本更新失效
8. **无认证** — API 未添加认证，生产环境需自行添加 API Key / JWT
9. **SQLite 并发** — 高并发场景需替换为 PostgreSQL
