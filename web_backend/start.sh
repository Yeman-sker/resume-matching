#!/bin/bash
cd "$(dirname "$0")"
PROJECT_DIR="$(cd .. && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "错误：未找到统一 Python 环境，请先运行 scripts/setup_python_env.sh"
    exit 1
fi

exec "$PYTHON" main.py
