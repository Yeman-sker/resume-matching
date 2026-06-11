#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

export JAVA_HOME="${JAVA_HOME:-/opt/jdk8}"
export HADOOP_HOME="${HADOOP_HOME:-/usr/local/hadoop}"
export SPARK_HOME="${SPARK_HOME:-/usr/local/spark}"
export PATH="$HOME/.local/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH"

if [ ! -x ".venv/bin/python" ]; then
    echo "错误：未找到统一 Python 环境，请先运行 scripts/setup_python_env.sh"
    exit 1
fi

echo "=== 启动简历匹配系统 ==="
echo ""

echo "启动数据生成器..."
(cd "$PROJECT_DIR/data_generator" && exec bash start.sh) &

echo "启动 Streaming 处理..."
(cd "$PROJECT_DIR/streaming" && exec bash streaming_supervisor.sh) &

echo "启动批处理调度器..."
(cd "$PROJECT_DIR/batch_processing" && exec bash start.sh) &

echo "启动 Web 后端..."
(cd "$PROJECT_DIR/web_backend" && exec bash start.sh) &

echo "启动前端..."
(cd "$PROJECT_DIR/frontend" && exec npm run dev -- --host 0.0.0.0) &

echo ""
echo "所有服务已启动："
echo "  数据生成器: http://localhost:8000"
echo "  批处理调度器: 后台运行"
echo "  Web 后端: http://localhost:8002"
echo "  前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

wait
