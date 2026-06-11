# 简历匹配系统 - Web 后端

基于 FastAPI + WebSocket 的后端 API 服务。

## 功能

- **WebSocket 实时推送**：每 2 秒推送系统状态
- **HDFS 数据统计**：统计简历/岗位/匹配数量
- **CORS 支持**：允许前端跨域访问

## 安装

```bash
bash scripts/setup_python_env.sh
```

## 启动

```bash
bash web_backend/start.sh
```

或手动启动：

```bash
.venv/bin/python web_backend/main.py
```

## 端口

- HTTP API: http://localhost:8002
- WebSocket: ws://localhost:8002/ws

## API 接口

### 1. 根路径
```bash
GET http://localhost:8002/
```

响应：
```json
{
  "message": "简历匹配系统 - Web 后端 API"
}
```

### 2. WebSocket 实时推送

连接地址：
```
ws://localhost:8002/ws
```

推送频率：每 2 秒

推送数据示例：
```json
{
  "data_generator_running": false,
  "streaming_running": false,
  "batch_running": false,
  "total_resumes": 150,
  "total_jobs": 120,
  "total_matches": 18000,
  "last_update": "2026-06-11 15:30:45"
}
```

## API 文档

启动后访问：http://localhost:8002/docs
