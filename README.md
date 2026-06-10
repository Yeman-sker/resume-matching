# 简历-岗位人才匹配系统

基于大数据（Hadoop + Spark）和 AI（OpenAI API + TF-IDF + Word2Vec）的教学项目。

## 快速开始

### 1. 初始化 HDFS
```bash
bash scripts/init_hdfs.sh
```

### 2. 启动数据生成器
```bash
export OPENAI_API_KEY="your-key"
cd data_generator
bash start.sh
```

启动生成器：
```bash
curl -X POST http://localhost:8000/control -H "Content-Type: application/json" -d '{"action":"start"}'
```

## 项目结构

```
├── data_generator/      # 上游：数据生成服务（FastAPI）
├── streaming/           # 中游：Spark Streaming 任务
├── batch_processing/    # 中游：批处理任务
├── frontend/            # 下游：React 前端
└── scripts/             # 工具脚本
```

## 技术栈

- Hadoop HDFS 3.3.6
- Apache Spark 3.5.1
- Python 3.10+ (FastAPI, PySpark)
- React 18 + Ant Design 5

## 文档

- [PRD.md](./PRD.md) - 完整产品需求文档
- [CLAUDE.md](./CLAUDE.md) - 项目开发指南
- [data_generator/README.md](./data_generator/README.md) - 数据生成器文档

## 开发状态

- [x] 上游数据生成服务
- [ ] 中游 Streaming 处理
- [ ] 中游批处理任务
- [ ] 下游 Web 前端
- [ ] 下游 Web 后端
