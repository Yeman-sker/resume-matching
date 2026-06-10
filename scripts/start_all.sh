#!/bin/bash

cd "$(dirname "$0")/.."

echo "=== 启动简历匹配系统 ==="
echo ""

echo "启动数据生成器..."
cd data_generator && bash start.sh &
cd ..

echo "启动 Streaming 处理..."
cd streaming && bash streaming_supervisor.sh &
cd ..

echo "启动批处理调度器..."
cd batch_processing && bash start.sh &
cd ..

echo "启动 Web 后端..."
cd web_backend && bash start.sh &
cd ..

echo "启动前端..."
cd frontend && npm run dev &
cd ..

echo ""
echo "所有服务已启动："
echo "  数据生成器: http://localhost:8000"
echo "  批处理调度器: 后台运行"
echo "  Web 后端: http://localhost:8002"
echo "  前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

wait
