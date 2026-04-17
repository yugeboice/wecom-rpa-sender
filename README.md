# WeCom RPA Sender — 企业微信桌面消息发送 RPA 执行器

## 项目背景

在企业客服场景中，AI Agent 需要通过企业微信向客户发送消息。但企业微信没有开放个人消息发送的 API，只能通过桌面客户端手动操作。

**WeCom RPA Sender** 解决了这个问题：它是一个 **RPA（Robotic Process Automation）执行器**，通过模拟键鼠操作来控制企业微信桌面客户端，实现自动发送消息。上游系统（如 AI Agent）只需调用一个 HTTP API，本服务就会自动完成「打开企业微信 → 搜索联系人 → 输入消息 → 点击发送」的完整流程。

### 架构

```
客服 Agent → REST API → 任务入库 → Scheduler 扫描 → RPA 执行 → 状态回写
```

### MVP 功能范围

- ✅ 通过 REST API 提交消息发送任务
- ✅ RPA 自动操控企业微信桌面客户端发送消息
- ✅ 支持 Windows 和 macOS 双平台
- ✅ 任务状态追踪（pending → running → success/failed）
- ✅ 自动重试失败任务（最多 3 次）
- ✅ 定时任务：设置 `planned_at` 字段，Scheduler 到期自动执行
- ✅ 幂等性支持（相同 idempotency_key 不会重复发送）
- ✅ 每步操作自动截图，方便排查问题
- ✅ 用户 ID 到企业微信搜索关键字的映射

---

## 环境要求

| 要求 | 说明 |
|------|------|
| **Python** | 3.10 或以上 |
| **操作系统** | macOS 12+ 或 Windows 10+ |
| **企业微信** | 桌面客户端已安装并登录 |
| **屏幕** | 需要有显示器（RPA 需要操控 GUI，不能在无头服务器上运行） |

### macOS 额外要求

- 需要授予终端/IDE **辅助功能权限**（System Settings → Privacy & Security → Accessibility）
- 企业微信应用名称默认为 `企业微信`（如果你使用英文版，需要在 `.env` 中修改 `WECOM_WINDOW_TITLE`）

### Windows 额外要求

- 不需要额外权限配置
- 企业微信窗口标题默认为 `企业微信`

---

## 安装步骤

### macOS

```bash
# 1. 克隆仓库
git clone https://github.com/yugeboice/wecom-rpa-sender.git
cd wecom-rpa-sender

# 2. 创建虚拟环境
python3 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 复制配置文件
cp .env.example .env
mkdir -p data screenshots logs config
cp app/config/user_mapping.json config/user_mapping.json

# 6. 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

或者使用一键脚本：

```bash
git clone https://github.com/yugeboice/wecom-rpa-sender.git
cd wecom-rpa-sender
chmod +x scripts/*.sh
bash scripts/setup.sh
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Windows

```powershell
# 1. 克隆仓库
git clone https://github.com/yugeboice/wecom-rpa-sender.git
cd wecom-rpa-sender

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
.venv\Scripts\activate.bat

# 4. 安装依赖
pip install -r requirements.txt

# 5. 复制配置文件
copy .env.example .env
mkdir data screenshots logs config
copy app\config\user_mapping.json config\user_mapping.json

# 6. 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

或者使用一键脚本：

```powershell
git clone https://github.com/yugeboice/wecom-rpa-sender.git
cd wecom-rpa-sender
scripts\setup.bat
.venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 验证服务已启动

启动后你应该看到类似输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
```

在浏览器打开 http://127.0.0.1:8000/health ，应该看到：

```json
{"status": "ok"}
```

如果看到这个响应，说明服务已成功启动。

---

## 配置说明

### .env 文件

从 `.env.example` 复制而来，所有配置项及说明：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WECOM_WINDOW_TITLE` | `企业微信` | 企业微信窗口标题。macOS 英文版可能是 `WeCom` |
| `RPA_STEP_DELAY` | `0.5` | RPA 每步操作间隔（秒），网络慢可以调大 |
| `RPA_SEARCH_WAIT` | `1.0` | 搜索后等待结果的时间（秒） |
| `RPA_SEND_WAIT` | `0.5` | 输入消息后等待的时间（秒） |
| `MAX_RETRY_COUNT` | `3` | 任务失败最大重试次数 |
| `RETRY_DELAY_SECONDS` | `30` | 重试间隔（秒） |
| `SCHEDULER_INTERVAL` | `5` | 后台扫描任务间隔（秒） |
| `DATABASE_URL` | `sqlite:///./data/tasks.db` | 数据库路径 |
| `SCREENSHOT_DIR` | `./screenshots` | 截图保存目录 |
| `LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `API_HOST` | `0.0.0.0` | API 监听地址 |
| `API_PORT` | `8000` | API 监听端口 |

### config/user_mapping.json

用户 ID 到企业微信搜索关键字的映射。RPA 会用这个关键字在企业微信搜索框中搜索联系人。

```json
{
  "_comment": "user_id -> 企业微信搜索关键字的映射表",
  "user_001": "张三",
  "user_002": "李四",
  "user_003": "王五"
}
```

- **key**：你的系统中的用户 ID（任意字符串）
- **value**：该用户在企业微信中的名称或搜索关键字
- `_comment` 字段会被自动忽略

**如何测试？** 把 value 改成你企业微信通讯录中一个真实联系人的名称。

---

## API 文档

服务启动后，完整的交互式 API 文档可以在浏览器访问：

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### API 接口一览

#### 1. 健康检查

```
GET /health
```

**响应：**

```json
{"status": "ok"}
```

#### 2. 创建发送任务

```
POST /api/v1/tasks
Content-Type: application/json
```

**请求体：**

```json
{
  "target_user_id": "user_001",
  "message_text": "你好，这是一条测试消息",
  "idempotency_key": "unique-key-12345",
  "business_type": "customer_service",
  "target_display_name": "张三",
  "trigger_type": "api",
  "planned_at": null,
  "payload": null
}
```

**参数说明：**

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `target_user_id` | ✅ | string | 目标用户 ID，对应 user_mapping.json 中的 key |
| `message_text` | ✅ | string | 要发送的消息内容 |
| `idempotency_key` | ✅ | string | 幂等键，相同 key 不会重复创建任务 |
| `business_type` | ❌ | string | 业务类型，默认 `customer_service` |
| `target_display_name` | ❌ | string | 备用显示名称（user_mapping 中没有时使用） |
| `trigger_type` | ❌ | string | 触发类型：`api`（默认）或 `scheduler` |
| `planned_at` | ❌ | datetime | 定时发送时间（ISO 8601 格式，如 `2026-04-18T09:00:00`），为空则立即发送 |
| `payload` | ❌ | object | 附加数据（JSON 对象），当前版本不使用 |

**响应（201）：**

```json
{
  "task_id": "a1b2c3d4e5f6...",
  "status": "success",
  "target_user_id": "user_001",
  "target_display_name": "张三",
  "message_text": "你好，这是一条测试消息",
  "business_type": "customer_service",
  "idempotency_key": "unique-key-12345",
  "trigger_type": "api",
  "retry_count": 0,
  "planned_at": null,
  "sent_at": "2026-04-17T12:00:00",
  "failure_reason": null,
  "created_at": "2026-04-17T12:00:00",
  "updated_at": "2026-04-17T12:00:00"
}
```

#### 3. 查询单个任务

```
GET /api/v1/tasks/{task_id}
```

**响应（200）：** 同上 TaskResponse 格式。

**响应（404）：**

```json
{"detail": "Task not found"}
```

#### 4. 查询任务列表

```
GET /api/v1/tasks?status=success&target_user_id=user_001&business_type=demo&limit=20&offset=0
```

所有 query 参数都是可选的。

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 按状态过滤：`pending` / `running` / `success` / `failed` |
| `target_user_id` | string | 按目标用户 ID 过滤 |
| `business_type` | string | 按业务类型过滤 |
| `limit` | int | 返回数量上限，默认 20，最大 100 |
| `offset` | int | 分页偏移量，默认 0 |

**响应（200）：** TaskResponse 数组。

#### 5. 重试失败任务

```
POST /api/v1/tasks/{task_id}/retry
```

仅对 `failed` 状态的任务有效。会重置重试次数并重新执行。

**响应（200）：** TaskResponse 格式。

**响应（400）：**

```json
{"detail": "Only failed tasks can be retried"}
```

### 任务状态机

```
pending → running → success
                  → failed (retry_count < max → 自动重试回 pending)
                         (retry_count >= max → 终态 failed)
```

---

## 测试指南

### 测试前置条件

1. **服务已启动** — 按上面的安装步骤启动服务，确认 http://127.0.0.1:8000/health 返回 `{"status": "ok"}`
2. **企业微信已登录** — 桌面客户端已打开并登录（仅 RPA 实际发送测试需要）
3. **macOS 辅助功能权限已授予** — macOS 用户需要给终端/IDE 授予 Accessibility 权限

### 测试 1：健康检查 API

**目的：** 验证服务正常运行。

```bash
curl http://127.0.0.1:8000/health
```

**预期响应：**

```json
{"status": "ok"}
```

**✅ 通过标准：** HTTP 200 且返回 `{"status": "ok"}`。

---

### 测试 2：创建发送任务

**目的：** 测试 API 创建任务功能。如果企业微信未启动，任务会创建成功但 RPA 执行会失败，这是正常的。

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": "user_001",
    "message_text": "你好，这是一条测试消息",
    "idempotency_key": "test-001"
  }'
```

**预期响应（HTTP 201）：**

```json
{
  "task_id": "...(一个32位hex字符串)...",
  "status": "failed",
  "target_user_id": "user_001",
  "message_text": "你好，这是一条测试消息",
  "idempotency_key": "test-001",
  "failure_reason": "...(企业微信未找到之类的错误信息)...",
  "..."
}
```

**✅ 通过标准：**
- HTTP 状态码 **201**（任务已创建）
- 返回的 JSON 包含 `task_id`、`status`、`message_text` 等字段
- 如果企业微信未启动：status 为 `"failed"`，failure_reason 会提示找不到窗口 — **这说明 API 层工作正常**
- 如果企业微信已启动并登录：status 可能为 `"success"`

---

### 测试 3：幂等性验证

**目的：** 验证相同的 idempotency_key 不会创建重复任务。

```bash
# 用和测试 2 相同的 idempotency_key 再发一次
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": "user_001",
    "message_text": "这条不应该创建新任务",
    "idempotency_key": "test-001"
  }'
```

**✅ 通过标准：** 返回的 `task_id` 和测试 2 **完全相同**，说明幂等生效，没有创建新任务。

---

### 测试 4：查询任务状态

**目的：** 通过 task_id 查询任务详情。

```bash
# 把 <TASK_ID> 替换为测试 2 返回的 task_id 值
curl http://127.0.0.1:8000/api/v1/tasks/<TASK_ID>
```

**✅ 通过标准：** HTTP 200，返回该任务的完整信息，task_id 匹配。

---

### 测试 5：查询任务列表

```bash
curl "http://127.0.0.1:8000/api/v1/tasks"
```

**✅ 通过标准：** HTTP 200，返回一个 JSON 数组，包含之前创建的任务。

```bash
# 带过滤条件
curl "http://127.0.0.1:8000/api/v1/tasks?status=failed&limit=5"
```

**✅ 通过标准：** 只返回 status 为 failed 的任务。

---

### 测试 6：查询不存在的任务

```bash
curl http://127.0.0.1:8000/api/v1/tasks/nonexistent-id
```

**✅ 通过标准：** HTTP 404，返回 `{"detail": "Task not found"}`。

---

### 测试 7：RPA 实际发送消息（需要企业微信已登录）

> ⚠️ **注意：** 测试期间不要移动鼠标或切换窗口，否则 RPA 操作会被打断。

**前提：**
1. 企业微信桌面客户端已打开并登录
2. 修改 `config/user_mapping.json`，把 `user_001` 映射到一个你通讯录中**真实存在**的联系人名称
3. macOS 用户确认已授予辅助功能权限

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": "user_001",
    "message_text": "RPA 测试消息，请忽略",
    "idempotency_key": "rpa-test-001"
  }'
```

**观察过程（整个流程约 5-10 秒）：**
1. 企业微信窗口自动弹到前台
2. 搜索框自动打开（Cmd+F / Ctrl+F）
3. 自动输入联系人名称
4. 自动选择搜索结果第一项
5. 自动在聊天框输入消息
6. 自动按回车发送

**✅ 通过标准：**
- API 返回 `"status": "success"`
- `screenshots/` 目录下出现截图文件（每步一张，共约 6 张）
- 联系人确实收到了消息

---

### 测试 8：使用 demo.py 测试

```bash
# 确保虚拟环境已激活

# 默认发送给 user_001
python demo.py

# 指定用户和消息
python demo.py user_002 "这是通过demo发送的消息"
```

**✅ 通过标准：** 打印 `Status: 201` 和任务的 JSON 信息。

---

### 测试 9：运行单元测试

```bash
pip install pytest
python -m pytest tests/ -v
```

**✅ 通过标准：** 所有测试通过（PASSED）。单元测试通过 mock 绕过了实际的 RPA 操作，**不需要企业微信**。

---

### 测试 10：Swagger UI 交互测试

在浏览器打开 http://127.0.0.1:8000/docs ，可以直接在网页上点击 "Try it out" 测试所有 API。

---

## 常见问题

### macOS: "osascript is not allowed assistive access"

**解决：** System Settings → Privacy & Security → Accessibility → 添加你的终端应用（Terminal / iTerm2 / VS Code 等）。如果已添加还不行，尝试移除后重新添加，然后重启终端。

### macOS: pyautogui 报权限错误

**解决：** 同上，需要授予辅助功能权限。

### macOS: pyautogui 安装失败

**解决：** 先安装 pyobjc：
```bash
pip install pyobjc-core pyobjc
pip install -r requirements.txt
```

### "无法找到企业微信窗口"

**解决：** 确认企业微信桌面客户端已启动并登录。检查 `.env` 中的 `WECOM_WINDOW_TITLE` 是否和你的企业微信窗口标题一致。

### Windows: pip install 提示缺少 Visual C++ Build Tools

**解决：** 从 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 安装 Build Tools。

### 中文输入乱码

本项目通过剪贴板粘贴方式输入中文，避免了输入法兼容问题。如果仍有问题，检查系统剪贴板功能是否正常（手动 Ctrl+C / Cmd+C 复制粘贴测试）。

### 端口 8000 被占用

```bash
# 查看谁占用了 8000
# macOS / Linux:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# 改用其他端口启动
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

---

## 项目结构

```
wecom-rpa-sender/
├── main.py                      # FastAPI 应用入口，定义 lifespan、路由和健康检查
├── demo.py                      # 快速演示脚本，通过 httpx 调用 API 发送任务
├── requirements.txt             # Python 依赖列表
├── .env.example                 # 环境变量模板（复制为 .env 使用）
├── .gitignore                   # Git 忽略规则
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── __init__.py          # API 路由：创建任务、查询任务、重试任务
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Pydantic Settings 配置类（从 .env 加载）
│   │   └── user_mapping.json    # 用户 ID → 企业微信搜索关键字映射模板
│   ├── db/
│   │   └── __init__.py          # SQLite 数据库初始化（SQLAlchemy engine）
│   ├── models/
│   │   ├── __init__.py          # Pydantic 数据模型（TaskCreate / TaskResponse / TaskStatus）
│   │   └── task_orm.py          # SQLAlchemy ORM 模型（tasks 表定义）
│   ├── repositories/
│   │   └── __init__.py          # 数据库操作层（TaskRepository：CRUD + 查询）
│   ├── rpa/
│   │   └── __init__.py          # RPA 核心引擎：窗口激活、搜索联系人、输入消息、发送（跨平台）
│   ├── scheduler/
│   │   └── __init__.py          # APScheduler 定时扫描器：每 N 秒处理 pending/retryable 任务
│   └── services/
│       └── __init__.py          # 业务逻辑层：执行任务、处理重试、更新状态
├── scripts/
│   ├── setup.sh                 # macOS/Linux 一键安装脚本
│   ├── setup.bat                # Windows 一键安装脚本
│   ├── start.sh                 # macOS/Linux 启动脚本
│   └── start.bat                # Windows 启动脚本
├── tests/
│   ├── __init__.py
│   └── test_api.py              # API 单元测试（mock RPA，验证接口正确性）
├── data/                        # (运行时自动生成) SQLite 数据库文件
├── screenshots/                 # (运行时自动生成) RPA 每步操作的截图
└── config/                      # (安装时复制生成) 运行时配置
    └── user_mapping.json        # 实际使用的用户映射文件
```

---

## 跨平台实现说明

| 功能 | Windows | macOS |
|------|---------|-------|
| 激活窗口 | `ctypes.windll.user32` FindWindow + SetForegroundWindow | `osascript` AppleScript |
| 中文输入 | `pyperclip.copy` + `Ctrl+V` | `pyperclip.copy` + `Cmd+V` |
| 搜索快捷键 | `Ctrl+F` | `Cmd+F` |
| 剪贴板后端 | `pyperclip` 自动使用 win32 API | `pyperclip` 自动使用 pbcopy/pbpaste |

## 已知限制

1. **单实例** — RPA 操作会占用屏幕焦点，同一时刻只能执行一个发送任务
2. **搜索准确性** — 搜索关键字可能匹配到多个联系人，默认选第一个结果
3. **无发送确认** — 目前无法通过 RPA 验证消息是否真正发送成功（无 OCR），仅判断流程是否无异常
4. **中文输入依赖剪贴板** — 通过剪贴板粘贴输入中文，会覆盖用户剪贴板
5. **企业微信版本依赖** — 快捷键可能因版本更新失效
6. **无认证** — API 未添加认证，生产环境需自行添加 API Key / JWT
7. **SQLite 并发** — 高并发场景需替换为 PostgreSQL

## 技术栈

- **FastAPI** — Web 框架 + 自动生成 API 文档
- **SQLAlchemy + SQLite** — 任务持久化
- **APScheduler** — 后台定时任务扫描
- **pyautogui** — 跨平台键鼠自动化
- **pyperclip** — 剪贴板操作（解决中文输入问题）
- **osascript** (macOS) / **ctypes** (Windows) — 窗口激活
