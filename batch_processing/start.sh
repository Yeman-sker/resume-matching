#!/bin/bash
cd "$(dirname "$0")"
PROJECT_DIR="$(cd .. && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "错误：未找到统一 Python 环境，请先运行 scripts/setup_python_env.sh"
    exit 1
fi

export PYSPARK_DRIVER_PYTHON="$PYTHON"
export PYSPARK_PYTHON="$PYTHON"

exec "$PYTHON" batch_scheduler.py
