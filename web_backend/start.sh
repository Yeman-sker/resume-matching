#!/bin/bash
cd "$(dirname "$0")"
PROJECT_DIR="$(cd .. && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "错误：未找到统一 Python 环境，请先运行 scripts/setup_python_env.sh"
    exit 1
fi

# VM fallback: shared .venv may be missing pandas while the prepared AI env has it.
if ! "$PYTHON" -c "import pandas" >/dev/null 2>&1; then
    FALLBACK_PYTHON="$HOME/ai_env/bin/python"
    if [ -x "$FALLBACK_PYTHON" ] && "$FALLBACK_PYTHON" -c "import pandas" >/dev/null 2>&1; then
        PYTHON="$FALLBACK_PYTHON"
    fi
fi

exec "$PYTHON" main.py
