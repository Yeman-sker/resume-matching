# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个教学性的大数据+AI应用项目：**简历-岗位人才匹配系统**。

**核心目标**：
- 模拟真实招聘平台的数据生成→处理→展示全流程
- 使用大数据技术（HDFS、Spark Streaming、Spark 批处理）+ AI技术（OpenAI API、TF-IDF、Word2Vec）实现智能匹配

**系统架构**：上游数据生成 → 中游数据处理（Streaming + 批处理）→ 下游 Web 展示

## 技术栈

**基础设施**：
- Hadoop HDFS 3.3.6（伪分布式）
- Apache Spark 3.5.1（Standalone）
- Ubuntu 24.04
- OpenJDK 11

**Python 环境**：
- Python 3.10+
- 上游：FastAPI + OpenAI API
- 中游：PySpark 3.5.1 + jieba + scikit-learn + gensim
- 下游：FastAPI

**前端**：
- React 18 + Ant Design 5 + Zustand

## 开发命令

### 数据生成器（端口 8000）
```bash
cd data_generator
python3 data_generator.py
```

### Streaming 任务
```bash
cd streaming
bash streaming_supervisor.sh  # 自动重启监督脚本
```

### 批处理调度器（端口 8001）
```bash
cd batch_processing
python3 batch_scheduler.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev          # 开发模式
npm run build        # 生产构建
```

### 启动所有服务
```bash
bash scripts/start_all.sh
```

### 停止所有服务
```bash
bash scripts/stop_all.sh
```

### HDFS 操作
```bash
# 初始化目录结构
bash scripts/init_hdfs.sh

# 查看数据
hdfs dfs -ls /resume_matching/raw/resumes
hdfs dfs -ls /resume_matching/processed/resumes
hdfs dfs -ls /resume_matching/output/matches

# 清理 Checkpoint（修改 Streaming 代码后）
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_resumes/
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_jobs/
```

## 项目结构

```
/
├── data_generator/          # 上游：数据生成服务（FastAPI）
├── streaming/               # 中游：Spark Streaming 任务
├── batch_processing/        # 中游：批处理任务（APScheduler + PySpark）
├── frontend/                # 下游：React 前端
├── scripts/                 # 启动脚本
│   ├── init_hdfs.sh
│   ├── start_all.sh
│   └── stop_all.sh
└── logs/                    # 日志目录
```

## HDFS 目录结构

```
hdfs://localhost:9000/resume_matching/
├── raw/                     # 上游原始数据（脏数据）
│   ├── resumes/*.csv
│   └── jobs/*.csv
├── processed/               # Streaming 清洗后的数据
│   ├── resumes/*.csv
│   └── jobs/*.csv
├── models/                  # 训练的模型文件
│   ├── tfidf/
│   └── word2vec/
├── output/                  # 最终匹配结果
│   └── matches/match_results.csv
├── checkpoints/             # Streaming checkpoint
│   ├── streaming_resumes/
│   └── streaming_jobs/
└── resources/               # 配置资源
    ├── stopwords.json
    └── skill_alias.json
```

## 核心架构要点

### 上游：数据生成服务
- 调用 OpenAI 兼容 API 持续生成简历和岗位数据
- 故意生成脏数据（缺失值、重复ID、格式不统一）
- 每 60 秒将缓存数据刷新到 HDFS
- FastAPI 提供启停控制接口

### 中游：Streaming 处理
- **轻量级实时处理**：监听 HDFS raw/ 目录新文件
- 数据清洗：去重、缺失值填充、HTML清理
- 字段结构化：学历等级映射、经验年限提取、城市标准化
- 文本预处理：jieba 分词、停用词过滤、技能标准化
- 每 10 分钟自动重启，加载最新模型

### 中游：批处理任务
- **重量级模型训练和匹配计算**：每 10 分钟运行一次（APScheduler）
- 训练 TF-IDF 和 Word2Vec 模型
- 计算语义分（TF-IDF 60% + Word2Vec 40%）
- 计算规则分（技能40% + 学历20% + 经验15% + 城市10% + 薪资10% + 证书5%）
- 生成最终匹配结果（简历×岗位笛卡尔积）

### 下游：Web 展示
- 系统监控面板（WebSocket 实时推送）
- 数据生成器控制
- 岗位匹配查询（HR 视角）
- 简历推荐查询（求职者视角）
- 匹配详情页（分数详情 + 推荐理由）

## 匹配算法

### 总分计算公式
```
总分 = 语义分 × 0.60 + 规则分 × 0.40
```

### 语义分计算
```
语义分 = TF-IDF分 × 0.6 + Word2Vec分 × 0.4
```

### 规则分计算
```
规则分 = 技能分×0.40 + 学历分×0.20 + 经验分×0.15 + 城市分×0.10 + 薪资分×0.10 + 证书分×0.05
```

## 重要约定

1. **Streaming 任务重启策略**：每 10 分钟自动退出，外层 supervisor 脚本自动重启，从 checkpoint 恢复
2. **批处理调度**：APScheduler 每 10 分钟触发一次，训练模型 + 计算匹配分
3. **数据流向**：单向流动，上游→中游→下游，不回流
4. **模型版本管理**：模型文件名带版本号（如 `vectorizer_v15.pkl`）
5. **文件命名**：时间戳格式 `YYYY-MM-DD_HH-MM.csv`

## 开发注意事项

- 修改 Streaming 代码后必须清理对应的 checkpoint 目录
- 所有文本字段处理前先转字符串类型
- 技能字段用 JSON 数组格式存储（不是逗号分隔字符串）
- 分数范围统一为 0-100
- 余弦相似度 [-1,1] 转换为分数：`(similarity + 1) / 2 * 100`
- 推荐理由必须包含：共同技能、缺失技能、各维度是否满足

## 参考文档

- PRD.md：完整产品需求文档
- 学生项目任务书：项目背景和验收标准
