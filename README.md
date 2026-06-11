# 简历-岗位人才匹配系统

基于大数据（Hadoop + Spark）和 AI（OpenAI 兼容 API + TF-IDF + Word2Vec）的教学项目。

## 快速开始

### 1. 创建统一 Python 环境
```bash
bash scripts/setup_python_env.sh
```

### 2. 初始化 HDFS
```bash
bash scripts/init_hdfs.sh
```

### 3. 配置环境变量
```bash
export OPENAI_API_KEY="your-key"
export OPENAI_API_BASE="https://api.deepseek.com/v1"  # 或其他兼容接口
export OPENAI_MODEL="deepseek-chat"
```

### 4. 启动所有服务
```bash
bash scripts/start_all.sh
```

### 5. 启动数据生成器
```bash
curl -X POST http://localhost:8000/control -H "Content-Type: application/json" -d '{"action":"start"}'
```

## 访问地址

- 数据生成器: http://localhost:8000
- Web 后端: http://localhost:8002
- 前端: http://localhost:5173

## 项目结构

```
├── data_generator/      # 上游：数据生成服务（FastAPI + OpenAI 兼容 API）
├── streaming/           # 中游：Spark Streaming 实时清洗
├── batch_processing/    # 中游：批处理任务（模型训练 + 匹配计算）
├── web_backend/         # 下游：Web 后端（FastAPI + WebSocket）
├── frontend/            # 下游：React 前端
├── scripts/             # 启动和管理脚本
├── requirements.txt     # 统一 Python 依赖
└── .venv/               # 统一 Python 虚拟环境
```

## 技术栈

- Hadoop HDFS 3.3.6（伪分布式）
- Apache Spark 3.5.1（Standalone）
- Python 3.10+（FastAPI、PySpark MLlib、NumPy、jieba）
- React 19 + shadcn/ui + Zustand + Vite

## 核心功能

- **上游**：OpenAI 兼容 API 持续生成脏数据，每 60 秒刷新到 HDFS
- **中游 Streaming**：实时清洗数据（去重、HTML 清理、字段标准化、文本预处理）
- **中游批处理**：每 10 分钟训练 TF-IDF 和 Word2Vec 模型，计算匹配分数
- **下游**：React 前端 + FastAPI 后端，WebSocket 实时推送系统状态

## 文档

- [CLAUDE.md](./CLAUDE.md) - 项目开发指南（优先查看）
- [PRD.md](./PRD.md) - 完整产品需求文档
- [data_generator/README.md](./data_generator/README.md) - 数据生成器文档
- [streaming/README.md](./streaming/README.md) - Streaming 处理文档
- [batch_processing/README.md](./batch_processing/README.md) - 批处理文档
- [web_backend/README.md](./web_backend/README.md) - Web 后端文档

## 开发状态

- [x] 上游数据生成服务
- [x] 中游 Streaming 处理
- [x] 中游批处理任务
- [x] 下游 Web 后端
- [ ] 下游 Web 前端（基础框架已完成，业务功能开发中）
