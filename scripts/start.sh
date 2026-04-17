#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
