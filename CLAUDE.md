# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. Hard to reverse — the cost of changing your mind later is meaningful 
2. Surprising without context — a future reader will wonder "why did they do it this way?" 
3. The result of a real trade-off - there were genuine alternatives and you picked one for specific reasons

## 项目概述

这是一个教学性的大数据+AI应用项目：**简历-岗位人才匹配系统**。

**核心目标**：
- 模拟真实招聘平台的数据生成→处理→展示全流程
- 使用大数据技术（HDFS、Spark Streaming、Spark 批处理）+ AI技术（OpenAI 兼容 API、TF-IDF、Word2Vec）实现智能匹配

**系统架构**：上游数据生成 → 中游数据处理（Streaming + 批处理）→ 下游 Web 展示

## 技术栈

**基础设施**：
- Hadoop HDFS 3.3.6（伪分布式）
- Apache Spark 3.5.1（Standalone）
- Ubuntu 24.04
- OpenJDK 11

**Python 环境**（统一虚拟环境 `.venv`）：
- Python 3.10+
- 依赖：fastapi、uvicorn、httpx、pyspark、numpy、jieba、apscheduler
- 上游：FastAPI + OpenAI 兼容 API（通过环境变量配置）
- 中游：PySpark 3.5.1（Spark MLlib）+ jieba
- 下游：FastAPI + WebSocket

**前端**：
- React 19 + shadcn/ui (Radix UI + Tailwind CSS) + Zustand + Vite

## 开发命令

> **运行环境：以下所有命令必须在 Parallels 虚拟机里执行，不要在本机运行。**
> 本机项目目录与虚拟机 `/media/psf/resume-matching` 是 Parallels 共享目录（实时双向同步，无需上传）。
> SSH 连接：`ssh parallels@10.211.55.4`（免密）。运行裸 `hdfs`/`spark-submit` 等命令需用 login shell，例如 `ssh parallels@10.211.55.4 "bash -lc 'cd /media/psf/resume-matching && <命令>'"`，否则不在 PATH。
> 快捷方式：斜杠命令 `/vm-run <命令>` 会自动按上述规则在虚拟机里执行。

### 环境初始化
```bash
# 统一 Python 环境（所有模块共享）
bash scripts/setup_python_env.sh

# HDFS 目录初始化
bash scripts/init_hdfs.sh
```

### 数据生成器（端口 8000）
```bash
cd data_generator
bash start.sh
```

### Streaming 任务
```bash
cd streaming
bash streaming_supervisor.sh  # 自动重启监督脚本
```

### 批处理调度器（端口 8001）
```bash
cd batch_processing
bash start.sh  # APScheduler 每 10 分钟自动运行 + FastAPI 控制接口（手动触发/状态/暂停恢复）
```

### Web 后端（端口 8002）
```bash
cd web_backend
bash start.sh
```

### 前端开发（端口 5173）
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
# 查看数据
hdfs dfs -ls /resume_matching/raw/resumes
hdfs dfs -ls /resume_matching/processed/resumes
hdfs dfs -ls /resume_matching/output/matches

# 清理 Checkpoint（修改 Streaming 代码后必须执行）
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_resumes/
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_jobs/

# 重置 HDFS 完整目录结构
bash scripts/reset_hdfs_schema.sh
```

## 项目结构

```
/
├── data_generator/          # 上游：数据生成服务（FastAPI）
│   ├── data_generator.py    # 主服务，调用 OpenAI 兼容 API 生成脏数据
│   └── start.sh             # 启动脚本
├── streaming/               # 中游：Spark Streaming 实时清洗
│   ├── streaming_resumes.py # 简历数据清洗
│   ├── streaming_jobs.py    # 岗位数据清洗
│   ├── streaming_supervisor.sh  # 监督脚本（自动重启）
│   ├── stopwords.json       # 停用词表
│   └── skill_alias.json     # 技能别名映射
├── batch_processing/        # 中游：批处理任务（模型训练+匹配计算）
│   ├── batch_job.py         # 核心任务（TF-IDF、Word2Vec、评分计算）
│   ├── batch_scheduler.py   # APScheduler 调度器 + FastAPI 控制接口（端口 8001）
│   └── start.sh             # 启动脚本
├── web_backend/             # 下游：Web 后端服务（FastAPI + WebSocket）
│   ├── main.py              # 后端主服务（系统监控）
│   └── start.sh             # 启动脚本
├── frontend/                # 下游：React 前端
│   ├── src/                 # React 应用源码
│   ├── package.json
│   └── vite.config.ts
├── scripts/                 # 启动和管理脚本
│   ├── init_hdfs.sh         # HDFS 目录初始化
│   ├── setup_python_env.sh  # 统一虚拟环境创建
│   ├── start_all.sh         # 启动所有服务
│   ├── stop_all.sh          # 停止所有服务
│   └── reset_hdfs_schema.sh # 重置 HDFS 目录结构
├── logs/                    # 日志目录
├── requirements.txt         # 统一 Python 依赖
└── .venv/                   # 统一 Python 虚拟环境
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
│   ├── count_vectorizer/
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
- **端口**：8000
- **功能**：调用 OpenAI 兼容 API（可配置 base_url 和 model）持续生成简历和岗位数据
- **数据特点**：故意生成脏数据（缺失值、重复ID、格式不统一、HTML标签、多余空格等）
- **刷新策略**：每 60 秒将缓存数据批量写入 HDFS `/resume_matching/raw/`
- **API 接口**：`POST /control` (start/stop)、`GET /status`
- **环境变量**：
  - `OPENAI_API_BASE`：API 基础地址
  - `OPENAI_API_KEY`：API 密钥
  - `OPENAI_MODEL`：使用的模型名称（默认 deepseek-v4-flash）
  - `BATCH_SIZE`：每批生成数量（默认 20）
  - `GENERATION_INTERVAL`：生成间隔秒数（默认 10）
  - `FLUSH_INTERVAL`：刷新到 HDFS 间隔秒数（默认 60）

### 中游：Streaming 处理
- **轻量级实时清洗**：监听 HDFS `raw/` 目录新文件（每次处理 1 个文件）
- **数据清洗**：
  - 去重（按 ID 去重）
  - 缺失值填充（空 ID 过滤，其他字段填充默认值）
  - HTML 标签清理（正则去除 `<.*>`）
  - 多余空格归一化
- **字段结构化**：
  - 学历等级映射（博士=5、硕士=4、本科=3、大专=2、高中=1、未知=0）
  - 经验年限提取（支持中文数字"一年"、"三年以上"等）
  - 城市标准化（"南昌市" → "南昌"、"江西南昌" → "南昌"）
  - 技能列表去重和标准化（"Python, py, python" → "Python"）
  - 薪资范围解析（"8-12万/年" → min=8, max=12）
- **文本预处理**：
  - jieba 分词
  - 停用词过滤（从 HDFS 加载或使用默认列表）
  - 技能别名标准化（从 HDFS 加载或使用默认映射）
  - 生成 tokens（JSON 数组）和 clean_text（空格分隔）
- **自动重启**：每 10 分钟（600秒）自动退出，外层 `streaming_supervisor.sh` 自动重启
- **Checkpoint**：保存在 HDFS `/resume_matching/checkpoints/streaming_*`

### 中游：批处理任务
- **重量级模型训练和匹配计算**：通过 APScheduler 每 10 分钟自动触发（服务启动时不立即运行）
- **手动控制**（FastAPI，端口 8001）：`POST /trigger` 手动触发（运行中返回 409 互斥）、`GET /status` 状态查询（含上次运行结果/日志/下次自动运行时间）、`GET /progress` 实时进度（运行中的阶段事件 + 实时日志尾部，由 batch_job.py 向 stdout 输出 `##PROGRESS##{json}` 行上报）、`POST /schedule/pause|resume` 暂停/恢复自动调度；web_backend 以 `/api/batch/*` 代理，前端「批处理控制」页操作
- **跳过语义**：数据不足时 `batch_job.py` 以退出码 3 退出，状态显示为「跳过」（区别于成功/失败）
- **执行流程**：
  1. 读取 HDFS 清洗后的简历和岗位数据
  2. 使用 MLlib CountVectorizer + IDF 训练 TF-IDF 模型（vocabSize=500, minDF=2）
  3. 使用 MLlib 训练 Word2Vec 模型（vectorSize=100, windowSize=5, maxIter=30）
  4. 计算语义分（TF-IDF 60% + Word2Vec 40%）
  5. 计算规则分（技能、学历、经验、城市、薪资、证书）
  6. 生成简历×岗位笛卡尔积匹配结果
  7. 保存匹配结果和模型到 HDFS
- **模型版本管理**：MLlib 模型目录名带时间戳（如 `tfidf_v202606112315/`）
- **输出**：匹配结果保存到 HDFS `/resume_matching/output/matches`

### 下游：Web 展示
- **端口**：8002（后端）、5173（前端开发）
- **功能**：
  - 系统监控面板（WebSocket 实时推送，每 2 秒）
  - HDFS 数据统计（简历数、岗位数、匹配数）
  - 数据生成器控制（待实现）
  - 岗位匹配查询（HR 视角，待实现）
  - 简历推荐查询（求职者视角，待实现）
  - 匹配详情页（分数详情 + 推荐理由，待实现）
- **技术栈**：FastAPI + WebSocket + React + shadcn/ui

## 匹配算法

### 总分计算公式
```
总分 = 语义分×0.60 + 规则分×0.40
规则分 = 技能分×0.40 + 学历分×0.20 + 经验分×0.15 + 城市分×0.10 + 薪资分×0.10 + 证书分×0.05
```

### 语义分计算
```
语义分 = TF-IDF分×0.60 + Word2Vec分×0.40
```

### 各维度评分规则

**技能分**（0-100）：
- 必备技能匹配率 × 85 + 加分技能匹配个数 × 5（最多+15）
- 返回共同技能和缺失技能

**学历分**（0-100）：
- 满足要求：100
- 差1级：60
- 差2级及以上：30

**经验分**（0-100）：
- 满足要求：100
- 差1年：70
- 差2年：40
- 差3年及以上：20

**城市分**（0-100）：
- 城市匹配：100
- 城市不匹配：50
- 城市未知：60

**薪资分**（0-100）：
- 期望薪资 ≤ 岗位上限：100
- 岗位上限 ≥ 期望薪资 × 0.8：70
- 其他：40
- 薪资未知：60

**证书分**（0-100）：
- 有证书：100
- 无证书：60

## 重要约定

1. **统一虚拟环境**：所有 Python 模块共享项目根目录的 `.venv/` 虚拟环境，依赖统一管理在 `requirements.txt`
2. **Streaming 任务重启策略**：每 10 分钟（600秒）自动退出，外层 `streaming_supervisor.sh` 自动重启，从 checkpoint 恢复
3. **批处理调度**：APScheduler 每 10 分钟触发一次，训练模型 + 计算匹配分
4. **数据流向**：单向流动（上游→中游→下游），不回流
5. **模型版本管理**：MLlib 模型目录名带时间戳版本号（如 `tfidf_v202606112315/`）
6. **文件命名**：HDFS 中的 CSV 文件名格式为 `YYYY-MM-DD_HH-MM-SS_<random>.csv`
7. **Checkpoint 清理**：修改 Streaming 代码后必须清理对应的 checkpoint 目录，否则会使用旧的执行计划
8. **技能字段格式**：使用管道符 `|` 分隔（不是逗号），例如 `Python|SQL|Spark`
9. **Token 字段格式**：JSON 数组字符串，例如 `["Python", "数据分析", "机器学习"]`
10. **分数范围**：所有分数统一为 0-100
11. **余弦相似度转换**：`similarity_to_score = (cosine_similarity + 1) / 2 * 100`
12. **推荐理由生成**：必须包含共同技能、缺失技能、各维度是否满足的综合描述

## 开发注意事项

- 修改 Streaming 代码后必须清理对应的 checkpoint 目录（`hdfs dfs -rm -r /resume_matching/checkpoints/streaming_*`）
- 所有文本字段处理前先转字符串类型（防止 None 导致的错误）
- 技能字段用管道符 `|` 分隔，不是逗号
- Token 字段是 JSON 数组字符串，需要 `json.loads()` 解析
- 分数范围统一为 0-100
- 余弦相似度 [-1,1] 转换为分数：`(similarity + 1) / 2 * 100`
- 推荐理由必须包含：共同技能、缺失技能、各维度是否满足
- PySpark UDF 中不能直接访问外部变量，需要通过闭包或广播变量传递
- Streaming 任务的 `awaitTermination(600)` 保证每 10 分钟自动退出
- HDFS 文件操作使用 `hdfs dfs` 命令，不是 `hadoop fs`
- 所有模块启动前确保已创建统一虚拟环境（`bash scripts/setup_python_env.sh`）

## 参考文档

- PRD.md：完整产品需求文档
- 学生项目任务书：项目背景和验收标准
