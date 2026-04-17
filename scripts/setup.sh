#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# 创建虚拟环境（如不存在）
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt -q

# 复制配置（如不存在）
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please review settings"
fi

# 创建必要目录
mkdir -p data screenshots logs config

# 复制用户映射（如不存在）
if [ ! -f "config/user_mapping.json" ]; then
    cp app/config/user_mapping.json config/user_mapping.json
fi

echo "Setup complete. Run: source .venv/bin/activate && python -m uvicorn main:app --reload"
