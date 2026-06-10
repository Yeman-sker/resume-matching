#!/bin/bash

echo "=== 启动 Web 后端 ==="
cd web_backend
bash start.sh &
WEB_PID=$!
cd ..

echo "=== 启动前端 ==="
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "服务已启动："
echo "  前端: http://localhost:5174"
echo "  后端: http://localhost:8002"
echo "  API 文档: http://localhost:8002/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $WEB_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
