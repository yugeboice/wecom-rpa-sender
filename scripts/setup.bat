@echo off
cd /d "%~dp0\.."

REM 创建虚拟环境（如不存在）
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt -q

REM 复制配置（如不存在）
if not exist ".env" (
    copy .env.example .env
    echo Created .env from .env.example — please review settings
)

REM 创建必要目录
if not exist "data" mkdir data
if not exist "screenshots" mkdir screenshots
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM 复制用户映射（如不存在）
if not exist "config\user_mapping.json" (
    copy app\config\user_mapping.json config\user_mapping.json
)

echo Setup complete. Run: .venv\Scripts\activate.bat ^&^& python -m uvicorn main:app --reload
