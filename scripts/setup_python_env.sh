#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple}"

if [ -x "$VENV_DIR/bin/python" ]; then
    CURRENT_VERSION="$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [ "$CURRENT_VERSION" != "3.11" ]; then
        echo "错误：$VENV_DIR 使用 Python $CURRENT_VERSION，请先删除后重建。"
        exit 1
    fi
else
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3.11)"
    elif command -v uv >/dev/null 2>&1; then
        UV_BIN="$(command -v uv)"
        "$UV_BIN" python install 3.11
        PYTHON_BIN="$("$UV_BIN" python find 3.11)"
    elif [ -x "$HOME/.local/bin/uv" ]; then
        UV_BIN="$HOME/.local/bin/uv"
        "$UV_BIN" python install 3.11
        PYTHON_BIN="$("$UV_BIN" python find 3.11)"
    else
        echo "错误：未找到 Python 3.11。请先安装 Python 3.11 或 uv。"
        exit 1
    fi
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install \
    --index-url "$PIP_INDEX_URL" --timeout 120 --retries 5 --upgrade pip
"$VENV_DIR/bin/python" -m pip install \
    --index-url "$PIP_INDEX_URL" --timeout 120 --retries 5 \
    -r "$PROJECT_DIR/requirements.txt"

echo "Python 环境已就绪：$VENV_DIR"
"$VENV_DIR/bin/python" --version
