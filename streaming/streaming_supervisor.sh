#!/bin/bash
# Streaming 任务监督脚本（自动重启）

cd "$(dirname "$0")"

LOG_DIR="../logs"
mkdir -p "$LOG_DIR"

echo "启动 Streaming 监督脚本..."

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动简历 Streaming 任务..."
    spark-submit \
        --master local[*] \
        --driver-memory 2g \
        streaming_resumes.py >> "$LOG_DIR/streaming_resumes.log" 2>&1

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 简历 Streaming 任务退出，5秒后重启..."
    sleep 5
done &

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动岗位 Streaming 任务..."
    spark-submit \
        --master local[*] \
        --driver-memory 2g \
        streaming_jobs.py >> "$LOG_DIR/streaming_jobs.log" 2>&1

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 岗位 Streaming 任务退出，5秒后重启..."
    sleep 5
done &

echo "Streaming 监督脚本已启动（后台运行）"
echo "日志目录: $LOG_DIR"
echo ""
echo "停止方式："
echo "  pkill -f streaming_supervisor.sh"
echo "  pkill -f spark-submit"

wait
