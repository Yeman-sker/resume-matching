# 简历匹配系统 - Web 后端

基于 FastAPI + WebSocket 的后端 API 服务。

## 功能

- **WebSocket 实时推送**：每 2 秒推送系统状态
- **HDFS 数据统计**：统计简历/岗位/匹配数量

## 启动

```bash
bash start.sh
```

## 端口

- HTTP API: http://localhost:8002
- WebSocket: ws://localhost:8002/ws

## API 文档

启动后访问：http://localhost:8002/docs
