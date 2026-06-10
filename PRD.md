# 基于大数据+AI的简历-岗位人才匹配系统 PRD

**版本**: v1.0  
**日期**: 2026-06-09  
**作者**: 项目组

---

## 1. 项目概述

### 1.1 项目背景

本项目是一个教学性的大数据+AI应用项目，旨在构建一个**模拟真实招聘平台的简历-岗位匹配系统**。

系统通过以下技术实现智能匹配：
- 大数据技术：HDFS 分布式存储、Spark Streaming 实时处理、Spark 批处理
- AI 技术：OpenAI API 生成数据、TF-IDF 和 Word2Vec 语义分析、多维度规则匹配

### 1.2 项目目标

**核心目标**：
1. 模拟真实招聘系统的**数据生成→处理→展示**全流程
2. 展示大数据技术在实时场景中的应用能力
3. 实现可解释的智能匹配算法

**技术目标**：
- 上游：实时生成脏数据，模拟真实数据源
- 中游：Spark 流处理 + 批处理混合架构
- 下游：实时监控和匹配结果展示

### 1.3 与参考项目的对比

| 维度 | 参考项目 | 本项目（优化版） |
|-----|---------|----------------|
| 数据来源 | AI 一次性生成静态数据 | OpenAI API 持续生成流式数据 |
| 数据处理 | 离线批处理（12 步串行） | 流处理 + 批处理混合架构 |
| 模型训练 | 一次性训练 | 定期重训练（每 10 分钟） |
| 展示方式 | Streamlit 简单展示 | React + FastAPI 实时监控 |
| 部署环境 | 本地单机 | 虚拟机 + HDFS + Spark 集群 |

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         上游：数据生成层                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Data Generator Service (FastAPI + OpenAI API)           │   │
│  │  - 持续调用 OpenAI 兼容接口生成简历和岗位数据               │   │
│  │  - 生成带质量问题的脏数据（缺失值、重复、格式不统一）         │   │
│  │  - 按时间窗口聚合（每 1 分钟生成一个 CSV 文件）              │   │
│  │  - 提供 HTTP API 控制生成器启停和配置                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│                   HDFS: hdfs://resume_matching/raw/resumes/*.csv                 │
│                   HDFS: hdfs://resume_matching/raw/jobs/*.csv                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        中游：数据处理层                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Spark Structured Streaming (轻量级实时处理)              │   │
│  │  - 监听 hdfs://resume_matching/raw/ 目录的新文件                           │   │
│  │  - 数据清洗（去重、缺失值、异常值、HTML 清理）               │   │
│  │  - 字段结构化（学历等级、经验年限、城市标准化）              │   │
│  │  - 文本预处理（分词、停用词、技能标准化）                    │   │
│  │  - 输出到 hdfs://resume_matching/processed/                               │   │
│  │  - Checkpoint: hdfs://resume_matching/checkpoints/                        │   │
│  │  - 每 10 分钟自动重启，加载最新模型                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│                   HDFS: hdfs://resume_matching/processed/resumes/*.csv           │
│                   HDFS: hdfs://resume_matching/processed/jobs/*.csv              │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Batch Processing Service (APScheduler + PySpark)        │   │
│  │  - 定时任务：每 10 分钟执行一次                             │   │
│  │  - 读取 hdfs://resume_matching/processed/ 下的全量数据                     │   │
│  │  - 训练 TF-IDF 和 Word2Vec 模型                            │   │
│  │  - 计算语义分（TF-IDF + Word2Vec）                         │   │
│  │  - 计算规则分（技能/学历/经验/城市/薪资/证书）              │   │
│  │  - 生成最终匹配结果（简历×岗位笛卡尔积）                     │   │
│  │  - 输出到 hdfs://resume_matching/output/matches/                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│                   HDFS: hdfs://resume_matching/output/matches/*.csv              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        下游：展示层                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Web Application (React + FastAPI)                       │   │
│  │  - 系统监控面板（实时显示三层架构运行状态）                  │   │
│  │  - 数据生成器控制（启动/停止/速率配置）                      │   │
│  │  - 岗位匹配查询（点击岗位→查看匹配简历）                     │   │
│  │  - 简历推荐查询（点击简历→查看推荐岗位）                     │   │
│  │  - 匹配详情页（各维度分数、推荐理由）                        │   │
│  │  - WebSocket 实时推送系统状态                              │   │
│  │  - HTTP 轮询获取匹配结果数据                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈清单

| 层级 | 组件 | 技术栈 | 版本 |
|-----|------|--------|------|
| **基础设施** | 分布式存储 | Hadoop HDFS | 3.3.6 |
| | 分布式计算 | Apache Spark | 3.5.1 |
| | 操作系统 | Ubuntu | 24.04 |
| | JDK | OpenJDK | 11 |
| **上游** | 数据生成器 | Python + FastAPI | 3.10+ |
| | AI 接口 | OpenAI 兼容 API | - |
| | HTTP 客户端 | openai-python | 最新 |
| **中游** | 流处理 | PySpark Structured Streaming | 3.5.1 |
| | 批处理 | PySpark | 3.5.1 |
| | 任务调度 | APScheduler | 3.10+ |
| | 中文分词 | jieba | 0.42+ |
| | 机器学习 | scikit-learn | 1.3+ |
| | 词向量 | gensim | 4.3+ |
| **下游** | 前端框架 | React | 18+ |
| | UI 组件库 | Ant Design | 5+ |
| | 状态管理 | Zustand | 4+ |
| | HTTP 客户端 | axios | 1.6+ |
| | 后端框架 | FastAPI | 0.100+ |
| | 静态文件服务 | nginx 或 Python http.server | - |

### 2.3 部署架构

**虚拟机环境**：
- 操作系统：Ubuntu 24.04
- 内存：8GB+
- CPU：4 核+
- 磁盘：50GB+

**部署模式**：单节点伪分布式 Hadoop + Spark Standalone

**服务端口分配**：
```
8000  - 数据生成器 FastAPI 服务
8001  - 批处理调度器 FastAPI 服务
3000  - React 前端服务
9000  - HDFS NameNode
8080  - Spark Master Web UI
4040  - Spark Application UI
```

**HDFS 目录结构**：

```
hdfs://localhost:9000/resume_matching
├── raw/                          # 上游原始数据
│   ├── resumes/                  # 简历数据
│   │   ├── 2026-06-09_14-30.csv
│   │   └── 2026-06-09_14-31.csv
│   └── jobs/                     # 岗位数据
│       ├── 2026-06-09_14-30.csv
│       └── 2026-06-09_14-31.csv
├── processed/                    # Streaming 处理后的数据
│   ├── resumes/
│   └── jobs/
├── models/                       # 训练的模型文件
│   ├── tfidf/
│   │   ├── vectorizer_v1.pkl
│   │   ├── resume_matrix_v1.pkl
│   │   └── job_matrix_v1.pkl
│   └── word2vec/
│       ├── model_v1.bin
│       ├── resume_vectors_v1.pkl
│       └── job_vectors_v1.pkl
├── output/                       # 最终匹配结果
│   └── matches/
│       └── match_results.csv
├── checkpoints/                  # Streaming checkpoint
│   ├── streaming_resumes/
│   └── streaming_jobs/
└── resources/                    # 配置资源
    ├── stopwords.json
    └── skill_alias.json
```

---

## 3. 上游：数据生成服务

### 3.1 功能说明

数据生成服务是整个系统的数据源，负责**持续生成带有质量问题的简历和岗位数据**，模拟真实招聘平台的数据流入场景。

**核心特性**：
1. **持续流式生成**：系统运行期间自动生成新数据
2. **脏数据生成**：包含缺失值、重复 ID、格式不统一等质量问题
3. **时间窗口聚合**：每 1 分钟将生成的数据聚合成一个 CSV 文件
4. **可控性**：通过 HTTP API 控制启动/停止/配置

### 3.2 OpenAI API 调用方案

**接口类型**：OpenAI 兼容接口（非官方 OpenAI，可以是 DeepSeek、Qwen 等）

**调用参数**：

```python
{
  "model": "deepseek-chat",  # 或其他兼容模型
  "messages": [
    {"role": "system", "content": "你是一个数据生成助手"},
    {"role": "user", "content": RESUME_GENERATION_PROMPT}
  ],
  "temperature": 0.9,  # 高温度保证数据多样性
  "max_tokens": 4000
}
```

**提示词来源**：参考 `workflow/01_ai_generate_dirty_data/AI生成脏数据提示词.md`

**简历生成提示词要点**：

- 生成 1-3 条简历数据
- CSV 格式，字段：`resume_id,name,gender,age,education,school,major,years_experience,skills,certifications,work_history,expected_salary,location,contact`
- 故意包含脏数据：5-10% 缺失值、3-5% 重复 ID、格式不统一、异常值

**岗位生成提示词要点**：

- 生成 1 条岗位数据
- CSV 格式，字段：`job_id,job_title,department,location,education_required,experience_required,skills_required,skills_preferred,salary_range,job_description,responsibilities,requirements`
- 故意包含脏数据（同简历）

### 3.3 数据生成策略

**生成频率**：
- 简历：每 30 秒生成 1-3 条（可配置）
- 岗位：每 60 秒生成 1 条（可配置）

**时间窗口聚合**：
- 数据生成后先缓存在内存中
- 每 60 秒将缓存的数据刷新到 HDFS
- 文件命名：`{timestamp}.csv`，例如 `2026-06-09_14-30.csv`

**伪代码**：

```python
class DataGenerator:
    def __init__(self):
        self.resume_buffer = []
        self.job_buffer = []
        self.last_flush_time = time.time()
        self.running = False
    
    def generate_loop(self):
        while self.running:
            # 每 30 秒生成简历
            if random.random() < 0.5:  # 50% 概率
                new_resumes = call_openai_api(RESUME_PROMPT, count=random.randint(1,3))
                self.resume_buffer.extend(new_resumes)
            
            # 每 60 秒刷新到 HDFS
            if time.time() - self.last_flush_time >= 60:
                self.flush_to_hdfs()
                self.last_flush_time = time.time()
            
            time.sleep(30)
    
    def flush_to_hdfs(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        if self.resume_buffer:
            save_to_hdfs(self.resume_buffer, f"hdfs://resume_matching/raw/resumes/{timestamp}.csv")
            self.resume_buffer.clear()
```

### 3.4 HDFS 输出路径

**简历数据**：`hdfs://localhost:9000/resume_matching/raw/resumes/{timestamp}.csv`

**岗位数据**：`hdfs://localhost:9000/resume_matching/raw/jobs/{timestamp}.csv`

**文件示例**：
```
hdfs://resume_matching/raw/resumes/2026-06-09_14-30.csv  (包含 14:30-14:31 之间生成的 6 条简历)
hdfs://resume_matching/raw/resumes/2026-06-09_14-31.csv  (包含 14:31-14:32 之间生成的 4 条简历)
hdfs://resume_matching/raw/jobs/2026-06-09_14-30.csv     (包含 14:30-14:31 之间生成的 1 条岗位)
```

### 3.5 控制 API 接口定义

**Base URL**: `http://虚拟机IP:8000`

#### 3.5.1 启动生成器

```
POST /api/generator/start
```

**请求体**：
```json
{
  "resume_interval_seconds": 30,  // 简历生成间隔
  "job_interval_seconds": 60,     // 岗位生成间隔
  "flush_interval_seconds": 60    // 刷新到 HDFS 的间隔
}
```

**响应**：
```json
{
  "status": "success",
  "message": "Data generator started",
  "config": {
    "resume_interval_seconds": 30,
    "job_interval_seconds": 60,
    "flush_interval_seconds": 60
  }
}
```

#### 3.5.2 停止生成器

```
POST /api/generator/stop
```

**响应**：
```json
{
  "status": "success",
  "message": "Data generator stopped"
}
```

#### 3.5.3 查询状态

```
GET /api/generator/status
```

**响应**：
```json
{
  "running": true,
  "total_resumes_generated": 1234,
  "total_jobs_generated": 456,
  "current_buffer_size": {
    "resumes": 3,
    "jobs": 1
  },
  "last_flush_time": "2026-06-09 14:30:00",
  "generation_rate": {
    "resumes_per_minute": 3.2,
    "jobs_per_minute": 1.0
  }
}
```

#### 3.5.4 查询统计信息

```
GET /api/generator/stats
```

**响应**：
```json
{
  "total_resumes": 1234,
  "total_jobs": 456,
  "files_created": {
    "resumes": 120,
    "jobs": 120
  },
  "hdfs_usage_mb": 45.6,
  "uptime_seconds": 7200
}
```

---

## 4. 中游：数据处理服务

### 4.1 Spark Structured Streaming 任务

#### 4.1.1 功能说明

Streaming 任务负责**轻量级的实时数据处理**，将原始脏数据转换为结构化、标准化的干净数据。

**处理流程**：
```
监听 hdfs://resume_matching/raw/ → 数据清洗 → 字段结构化 → 文本预处理 → 输出到 hdfs://resume_matching/processed/
```

#### 4.1.2 输入/输出路径

**输入**：
- 简历：`hdfs://localhost:9000/resume_matching/raw/resumes/*.csv`
- 岗位：`hdfs://localhost:9000/resume_matching/raw/jobs/*.csv`
- 停用词表：`hdfs://localhost:9000/resume_matching/resources/stopwords.json`
- 技能标准化表：`hdfs://localhost:9000/resume_matching/resources/skill_alias.json`

**输出**：

- 简历：`hdfs://localhost:9000/resume_matching/processed/resumes/*.csv`
- 岗位：`hdfs://localhost:9000/resume_matching/processed/jobs/*.csv`

**Checkpoint**：

- 简历流：`hdfs://localhost:9000/resume_matching/checkpoints/streaming_resumes/`
- 岗位流：`hdfs://localhost:9000/resume_matching/checkpoints/streaming_jobs/`

#### 4.1.3 处理步骤

**步骤 1：数据清洗**（参考 `workflow/03_clean_data/`）
- 按主键去重（`resume_id`、`job_id`）
- 缺失值填充：文本字段填充空字符串，数值字段填充 0 或中位数
- 异常值处理：年龄 < 16 或 > 65 用中位数填充，薪资 < 0 或 > 100 填充为 0
- HTML 标签清理：使用正则表达式移除 `<.*?>`
- 空白压缩：连续空白符替换为单个空格

**步骤 2：字段结构化**（参考 `workflow/04_structure_data/`）
- 学历等级映射：`{"大专": 3, "本科": 4, "硕士": 5, "博士": 6}`
- 经验年限提取：`"1-3年" → 2`，`"三年以上" → 3`
- 城市标准化：`"南昌市" → "南昌"`，`"江西南昌" → "南昌"`
- 薪资解析：`"8-12万/年" → (8, 12)`
- 技能切分：`"Python, SQL, Spark" → ["Python", "SQL", "Spark"]`

**步骤 3：文本预处理**（参考 `workflow/06_preprocess_text/`）
- 分词：使用 jieba 对文本字段分词
- 停用词过滤：基于 `stopwords.json` 过滤
- 技能标准化：基于 `skill_alias.json` 统一技能词（`"py" → "Python"`）
- 生成字段：
  - `tokens`: 分词后的列表
  - `clean_text`: 过滤停用词后的文本
  - `standard_skills`: 标准化后的技能列表

**输出字段示例**（简历）：
```csv
resume_id,name,gender,age,education,education_level,school,major,years_experience,experience_years_num,skills,standard_skills,certifications,work_history,expected_salary,location,standard_location,contact,tokens,clean_text
RES_001,张三,男,25,本科,4,南昌大学,计算机,1-3年,2,"Python,SQL","[""Python"",""SQL""]",无,xxx项目经验,10,南昌,南昌,xxx@email.com,"[""Python"",""SQL"",...]","Python SQL 数据分析..."
```

#### 4.1.4 Checkpoint 策略

**启用 HDFS checkpoint**：
```python
query = (stream
    .writeStream
    .format("csv")
    .option("path", "hdfs://localhost:9000/resume_matching/processed/resumes/")
    .option("checkpointLocation", "hdfs://localhost:9000/resume_matching/checkpoints/streaming_resumes/")
    .outputMode("append")
    .start())
```

**重启策略**：
- Streaming 任务每 10 分钟自动退出
- 外层 supervisor 脚本自动重启任务
- 重启时从 checkpoint 恢复，确保不丢失、不重复处理数据

**Checkpoint 清理**：
- 如果修改 Streaming 代码导致不兼容，手动清理：
  ```bash
  hdfs dfs -rm -r /resume_matching/checkpoints/streaming_resumes/
  hdfs dfs -rm -r /resume_matching/checkpoints/streaming_jobs/
  ```

#### 4.1.5 启动脚本

**streaming_supervisor.sh**：
```bash
#!/bin/bash
while true; do
    echo "[$(date)] Starting Spark Streaming job..."
    spark-submit \
        --master local[*] \
        --conf spark.sql.streaming.schemaInference=true \
        streaming_job.py
    
    echo "[$(date)] Streaming job exited. Restarting in 5 seconds..."
    sleep 5
done
```

### 4.2 批处理任务

#### 4.2.1 功能说明

批处理任务负责**重量级的模型训练和匹配计算**，每 10 分钟运行一次。

**核心职责**：
1. 使用全量数据训练 TF-IDF 和 Word2Vec 模型
2. 计算语义分（TF-IDF 相似度 + Word2Vec 相似度）
3. 计算规则分（6 个维度的规则匹配分数）
4. 生成最终匹配结果（简历×岗位笛卡尔积）

#### 4.2.2 调度策略

**调度器**：APScheduler（Python 后台任务调度）

**调度配置**：
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    run_batch_job,
    trigger='interval',
    minutes=10,
    id='batch_processing',
    replace_existing=True
)
scheduler.start()
```

**服务端口**：8001

#### 4.2.3 模型训练

**TF-IDF 训练**（参考 `workflow/07_train_tfidf/`）：
```python
from sklearn.feature_extraction.text import TfidfVectorizer

# 读取全量数据
resumes = spark.read.csv("hdfs://resume_matching/processed/resumes/**/*.csv", header=True)
jobs = spark.read.csv("hdfs://resume_matching/processed/jobs/**/*.csv", header=True)

# 合并所有文本作为语料库
corpus = resumes.select("clean_text").union(jobs.select("clean_text"))

# 训练 TF-IDF
vectorizer = TfidfVectorizer(max_features=5000)
vectorizer.fit(corpus)

# 生成向量矩阵
resume_tfidf = vectorizer.transform(resumes["clean_text"])
job_tfidf = vectorizer.transform(jobs["clean_text"])

# 保存模型
save_to_hdfs(vectorizer, "hdfs://resume_matching/models/tfidf/vectorizer_v{version}.pkl")
save_to_hdfs(resume_tfidf, "hdfs://resume_matching/models/tfidf/resume_matrix_v{version}.pkl")
save_to_hdfs(job_tfidf, "hdfs://resume_matching/models/tfidf/job_matrix_v{version}.pkl")
```

**Word2Vec 训练**（参考 `workflow/08_train_word2vec/`）：
```python
from gensim.models import Word2Vec

# 训练 Word2Vec
sentences = [row["tokens"].split() for row in resumes.collect() + jobs.collect()]
w2v_model = Word2Vec(sentences, vector_size=100, window=5, min_count=2, workers=4)

# 生成文档向量（词向量平均）
def doc_vector(tokens, model):
    vectors = [model.wv[word] for word in tokens if word in model.wv]
    return np.mean(vectors, axis=0) if vectors else np.zeros(100)

resume_w2v = np.array([doc_vector(tokens, w2v_model) for tokens in resumes["tokens"]])
job_w2v = np.array([doc_vector(tokens, w2v_model) for tokens in jobs["tokens"]])

# 保存模型
w2v_model.save(f"hdfs://resume_matching/models/word2vec/model_v{version}.bin")
save_to_hdfs(resume_w2v, f"hdfs://resume_matching/models/word2vec/resume_vectors_v{version}.pkl")
save_to_hdfs(job_w2v, f"hdfs://resume_matching/models/word2vec/job_vectors_v{version}.pkl")
```

#### 4.2.4 匹配计算

**语义分计算**（参考 `workflow/09_calculate_semantic_scores/`）：
```python
from sklearn.metrics.pairwise import cosine_similarity

# 计算 TF-IDF 余弦相似度
tfidf_similarity = cosine_similarity(resume_tfidf, job_tfidf)  # shape: (n_resumes, n_jobs)

# 计算 Word2Vec 余弦相似度
w2v_similarity = cosine_similarity(resume_w2v, job_w2v)

# 转换为 0-100 分
tfidf_score = (tfidf_similarity + 1) / 2 * 100  # 余弦相似度 [-1,1] → [0,100]
word2vec_score = (w2v_similarity + 1) / 2 * 100

# 加权平均
semantic_score = 0.6 * tfidf_score + 0.4 * word2vec_score
```

**规则分计算**（参考 `workflow/10_calculate_rule_scores/`）：

详见第 7 章《核心算法》。

#### 4.2.5 输出格式

**最终匹配结果**：`hdfs://resume_matching/output/matches/match_results.csv`

**字段定义**：
```csv
resume_id,resume_name,job_id,job_title,department,
tfidf_score,word2vec_score,semantic_score,
skill_score,education_score,experience_score,city_score,salary_score,certificate_score,rule_score,
total_score,
matched_skills,missing_skills,reason
```

**输出模式**：`overwrite`（每次覆盖之前的结果）

---

## 5. 下游：Web 展示服务

### 5.1 功能模块

Web 界面包含 5 个核心功能模块：

#### 5.1.1 模块 A：系统监控面板（Dashboard）

**功能描述**：实时显示三层架构的运行状态和关键指标。

**展示内容**：

**上游区域**：
- 数据生成器状态：运行中 / 已停止
- 累计生成数据量：简历数、岗位数
- 生成速率：简历/分钟、岗位/分钟
- 最后刷新时间

**中游区域**：
- Streaming 任务状态：运行中 / 重启中
- 处理进度：已清洗简历数、岗位数
- 处理延迟：平均延迟秒数
- 批处理任务状态：上次运行时间、下次运行时间
- 模型版本：TF-IDF 版本、Word2Vec 版本

**下游区域**：
- 匹配结果总数
- 最后更新时间

**数据更新方式**：WebSocket 实时推送（每 2 秒）

#### 5.1.2 模块 B：数据生成器控制

**功能描述**：控制数据生成器的启停和配置。

**界面元素**：
- 启动按钮：调用 `POST /api/generator/start`
- 停止按钮：调用 `POST /api/generator/stop`
- 配置面板：
  - 简历生成间隔（秒）：输入框，默认 30
  - 岗位生成间隔（秒）：输入框，默认 60
  - 刷新间隔（秒）：输入框，默认 60
- 生成历史记录：最近生成的 10 条数据预览（表格形式）

**数据更新方式**：HTTP 轮询（每 5 秒）

#### 5.1.3 模块 C：岗位匹配查询

**功能描述**：HR 视角 - 点击岗位查看匹配的简历。

**页面布局**：
```
┌─────────────────┬───────────────────────────────────────┐
│   岗位列表       │        匹配的简历列表                   │
│  (左侧 30%)     │         (右侧 70%)                     │
│                 │                                        │
│ □ 技术部        │  选中岗位: JOB_001 - Python开发工程师   │
│ □ 数据部        │                                        │
│                 │  ┌────────────────────────────────┐   │
│ [JOB_001]       │  │ RES_001 - 张三   总分: 85.6     │   │
│ Python开发工程师│  │ 本科 | 2年 | Python, SQL, Spark│   │
│ 技术部 | 南昌   │  │ 语义分: 88.2 | 规则分: 82.0     │   │
│                 │  │ [查看详情]                      │   │
│ [JOB_002]       │  └────────────────────────────────┘   │
│ 数据分析师      │  ┌────────────────────────────────┐   │
│ 数据部 | 北京   │  │ RES_045 - 李四   总分: 78.3     │   │
│                 │  │ ...                             │   │
│ ...             │  └────────────────────────────────┘   │
└─────────────────┴───────────────────────────────────────┘
```

**岗位列表功能**：
- 显示所有岗位：岗位 ID、岗位名称、部门、城市
- 按部门筛选（多选框）
- 搜索框（按岗位名称）
- 点击岗位加载匹配简历

**简历列表功能**：
- 按总分降序排列（前 50 名）
- 显示关键信息：姓名、学历、经验、技能、总分
- 显示语义分和规则分
- 点击「查看详情」按钮展开详情页

**API 接口**：
- `GET /api/jobs` - 获取所有岗位
- `GET /api/jobs/{job_id}/matches?limit=50` - 获取匹配简历

#### 5.1.4 模块 D：简历推荐查询

**功能描述**：求职者视角 - 点击简历查看推荐的岗位。

**页面布局**：类似模块 C，左右调换

```
┌─────────────────┬───────────────────────────────────────┐
│   简历列表       │        推荐的岗位列表                   │
│  (左侧 30%)     │         (右侧 70%)                     │
│                 │                                        │
│ 搜索: [姓名]    │  选中简历: RES_001 - 张三               │
│                 │                                        │
│ [RES_001]       │  ┌────────────────────────────────┐   │
│ 张三            │  │ JOB_001 - Python开发工程师      │   │
│ 本科 | 2年      │  │ 技术部 | 南昌 | 8-12万/年       │   │
│ Python, SQL     │  │ 总分: 85.6                      │   │
│                 │  │ 推荐理由: 技能匹配度高、学历符合 │   │
│ [RES_002]       │  │ [查看详情]                      │   │
│ 李四            │  └────────────────────────────────┘   │
│ ...             │  ┌────────────────────────────────┐   │
│                 │  │ JOB_015 - 数据工程师            │   │
│                 │  │ ...                             │   │
│                 │  └────────────────────────────────┘   │
└─────────────────┴───────────────────────────────────────┘
```

**API 接口**：
- `GET /api/resumes` - 获取所有简历
- `GET /api/resumes/{resume_id}/recommendations?limit=50` - 获取推荐岗位

#### 5.1.5 模块 E：匹配详情页

**功能描述**：展示某个匹配对（简历×岗位）的详细分数和推荐理由。

**展示内容**：

**基本信息区**：
- 左侧：简历基本信息（姓名、学历、经验、技能、期望薪资、城市）
- 右侧：岗位基本信息（岗位名称、部门、要求、薪资范围、城市）

**分数详情区**：
```
总分: 85.6

语义分 (88.2) ━━━━━━━━━━━━━━━━━━ 60% 权重
├─ TF-IDF 分: 90.5
└─ Word2Vec 分: 84.8

规则分 (82.0) ━━━━━━━━━━━━━━━━━━ 40% 权重
├─ 技能匹配 (90.0) ━━ 40% 权重
│   已匹配: Python, SQL, Pandas
│   缺失技能: Spark, Hadoop
├─ 学历匹配 (100.0) ━━ 20% 权重
├─ 经验匹配 (85.0) ━━ 15% 权重
├─ 城市匹配 (100.0) ━━ 10% 权重
├─ 薪资匹配 (70.0) ━━ 10% 权重
└─ 证书加分 (50.0) ━━ 5% 权重
```

**推荐理由区**：
```
推荐理由：
1. 技能匹配度高：候选人掌握 Python, SQL, Pandas 等核心技能，与岗位要求的 Python, SQL, Pandas, Spark 高度匹配
2. 学历完全符合：本科学历满足岗位最低学历要求（本科）
3. 工作经验符合：2 年经验满足岗位要求（1-3 年）
4. 地理位置匹配：期望工作城市（南昌）与岗位城市（南昌）一致
5. 薪资预期合理：期望薪资 10 万/年在岗位薪资范围 8-12 万/年之内
```

**API 接口**：
- `GET /api/matches/{resume_id}/{job_id}` - 获取详细匹配信息

### 5.2 页面布局设计

**顶部导航栏**：
```
┌──────────────────────────────────────────────────────────┐
│ [Logo] 简历-岗位匹配系统                                   │
│                                                           │
│ [系统监控] [岗位匹配] [简历推荐] [生成器控制]              │
└──────────────────────────────────────────────────────────┘
```

**技术实现**：React Router

### 5.3 数据更新机制

#### 5.3.1 WebSocket 实时推送（系统状态）

**连接地址**：`ws://虚拟机IP:8000/ws/status`

**推送频率**：每 2 秒

**推送数据格式**：
```json
{
  "timestamp": "2026-06-09 14:30:15",
  "generator": {
    "running": true,
    "total_resumes": 1234,
    "total_jobs": 456,
    "rate_per_minute": 3.2,
    "buffer_size": {"resumes": 3, "jobs": 1}
  },
  "streaming": {
    "running": true,
    "processed_resumes": 1200,
    "processed_jobs": 450,
    "latency_seconds": 5.3
  },
  "batch": {
    "last_run": "2026-06-09 14:20:00",
    "next_run": "2026-06-09 14:30:00",
    "model_version": {
      "tfidf": "v15",
      "word2vec": "v15"
    }
  },
  "output": {
    "total_matches": 55704,
    "last_update": "2026-06-09 14:20:30"
  }
}
```

**前端实现**：
```javascript
const ws = new WebSocket('ws://虚拟机IP:8000/ws/status')
ws.onmessage = (event) => {
  const status = JSON.parse(event.data)
  // 更新 Zustand store
  useSystemStore.setState({ status })
}
```

#### 5.3.2 HTTP 轮询/按需请求（业务数据）

**岗位列表**：页面加载时请求一次，后续每 30 秒轮询
```
GET /api/jobs
```

**简历列表**：页面加载时请求一次，后续每 30 秒轮询
```
GET /api/resumes
```

**匹配结果**：用户点击岗位/简历时按需请求（不轮询）
```
GET /api/jobs/{job_id}/matches
GET /api/resumes/{resume_id}/recommendations
```

### 5.4 后端 API 接口定义

**Base URL**: `http://虚拟机IP:8000`

#### 5.4.1 获取所有岗位

```
GET /api/jobs
```

**查询参数**：
- `department`: 按部门筛选（可选）
- `search`: 按岗位名称搜索（可选）

**响应**：
```json
{
  "total": 456,
  "jobs": [
    {
      "job_id": "JOB_001",
      "job_title": "Python开发工程师",
      "department": "技术部",
      "location": "南昌",
      "education_required": "本科",
      "experience_required": "1-3年",
      "salary_range": "8-12万/年"
    },
    ...
  ]
}
```

#### 5.4.2 获取岗位匹配的简历

```
GET /api/jobs/{job_id}/matches
```

**查询参数**：
- `limit`: 返回数量，默认 50

**响应**：
```json
{
  "job_id": "JOB_001",
  "job_title": "Python开发工程师",
  "total_matches": 1234,
  "matches": [
    {
      "resume_id": "RES_001",
      "name": "张三",
      "education": "本科",
      "years_experience": "2年",
      "skills": ["Python", "SQL", "Spark"],
      "total_score": 85.6,
      "semantic_score": 88.2,
      "rule_score": 82.0
    },
    ...
  ]
}
```

#### 5.4.3 获取所有简历

```
GET /api/resumes
```

**查询参数**：
- `search`: 按姓名搜索（可选）

**响应**：类似 `/api/jobs`

#### 5.4.4 获取简历推荐的岗位

```
GET /api/resumes/{resume_id}/recommendations
```

**响应**：类似 `/api/jobs/{job_id}/matches`

#### 5.4.5 获取匹配详情

```
GET /api/matches/{resume_id}/{job_id}
```

**响应**：
```json
{
  "resume": { /* 完整简历信息 */ },
  "job": { /* 完整岗位信息 */ },
  "scores": {
    "total_score": 85.6,
    "semantic_score": 88.2,
    "tfidf_score": 90.5,
    "word2vec_score": 84.8,
    "rule_score": 82.0,
    "skill_score": 90.0,
    "education_score": 100.0,
    "experience_score": 85.0,
    "city_score": 100.0,
    "salary_score": 70.0,
    "certificate_score": 50.0
  },
  "matched_skills": ["Python", "SQL", "Pandas"],
  "missing_skills": ["Spark", "Hadoop"],
  "reason": "推荐理由文本..."
}
```

---

## 6. 数据设计

### 6.1 HDFS 目录结构

详见第 2.3 节。

### 6.2 CSV 字段定义

#### 6.2.1 原始简历数据（raw/resumes/*.csv）

| 字段名 | 类型 | 说明 | 示例 |
|-------|------|------|------|
| resume_id | string | 简历唯一编号 | RES_001 |
| name | string | 姓名 | 张三 |
| gender | string | 性别 | 男 |
| age | int | 年龄 | 25 |
| education | string | 学历（可能不规范） | 本科、本科学历 |
| school | string | 毕业院校 | 南昌大学 |
| major | string | 专业 | 计算机科学与技术 |
| years_experience | string | 工作年限（可能不规范） | 1-3年、三年以上 |
| skills | string | 技能（逗号分隔，可能不规范） | Python,SQL,py |
| certifications | string | 证书（逗号分隔） | 无、CET-4 |
| work_history | string | 工作经历描述 | 某公司数据分析... |
| expected_salary | float | 期望年薪（万/年） | 10 |
| location | string | 期望城市（可能不规范） | 南昌、南昌市 |
| contact | string | 联系方式 | xxx@email.com |

#### 6.2.2 处理后简历数据（processed/resumes/*.csv）

在原始字段基础上新增：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| education_level | int | 学历等级（3-6） |
| experience_years_num | int | 经验年限数值 |
| standard_location | string | 标准化城市名 |
| standard_skills | json | 标准化后的技能列表 |
| tokens | json | 分词结果 |
| clean_text | string | 清洗后的文本 |

#### 6.2.3 原始岗位数据（raw/jobs/*.csv）

| 字段名 | 类型 | 说明 | 示例 |
|-------|------|------|------|
| job_id | string | 岗位唯一编号 | JOB_001 |
| job_title | string | 岗位名称 | Python开发工程师 |
| department | string | 所属部门 | 技术部 |
| location | string | 工作城市 | 南昌 |
| education_required | string | 最低学历要求 | 本科 |
| experience_required | string | 最低经验要求 | 1-3年 |
| skills_required | string | 必备技能 | Python,SQL,Spark |
| skills_preferred | string | 加分技能 | Hadoop,Hive |
| salary_range | string | 薪资范围 | 8-12万/年 |
| job_description | string | 岗位描述 | ... |
| responsibilities | string | 主要职责 | ... |
| requirements | string | 具体要求 | ... |

#### 6.2.4 处理后岗位数据（processed/jobs/*.csv）

在原始字段基础上新增：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| education_required_level | int | 学历要求等级 |
| experience_required_num | int | 经验要求数值 |
| standard_location | string | 标准化城市名 |
| required_skills_standard | json | 标准化必备技能 |
| preferred_skills_standard | json | 标准化加分技能 |
| salary_min | float | 最低薪资 |
| salary_max | float | 最高薪资 |
| tokens | json | 分词结果 |
| clean_text | string | 清洗后的文本 |

#### 6.2.5 最终匹配结果（output/matches/match_results.csv）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| resume_id | string | 简历编号 |
| resume_name | string | 简历姓名 |
| job_id | string | 岗位编号 |
| job_title | string | 岗位名称 |
| department | string | 岗位部门 |
| tfidf_score | float | TF-IDF 分数（0-100） |
| word2vec_score | float | Word2Vec 分数（0-100） |
| semantic_score | float | 语义分（0-100） |
| skill_score | float | 技能匹配分（0-100） |
| education_score | float | 学历匹配分（0-100） |
| experience_score | float | 经验匹配分（0-100） |
| city_score | float | 城市匹配分（0-100） |
| salary_score | float | 薪资匹配分（0-100） |
| certificate_score | float | 证书加分（0-100） |
| rule_score | float | 规则分（0-100） |
| total_score | float | 总分（0-100） |
| matched_skills | json | 已匹配的技能列表 |
| missing_skills | json | 缺失的技能列表 |
| reason | string | 推荐理由文本 |

### 6.3 停用词表和技能标准化表

#### 6.3.1 stopwords.json

**格式**：
```json
[
  "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
  "能", "说", "会", "要", "着", "看", "好", "用", "与", "及", "等"
]
```

**生成方式**：参考项目的步骤 5，基于初始数据分析生成

#### 6.3.2 skill_alias.json

**格式**：
```json
{
  "py": "Python",
  "python": "Python",
  "PYTHON": "Python",
  "sql": "SQL",
  "Sql": "SQL",
  "mysql": "MySQL",
  "MYSQL": "MySQL",
  "Apache Spark": "Spark",
  "pyspark": "Spark",
  "数据分析": "Data Analysis",
  "数据统计": "Data Analysis",
  "机器学习": "Machine Learning",
  "ML": "Machine Learning"
}
```

**生成方式**：参考项目的步骤 5，基于初始数据中的技能词频分析生成

---

## 7. 核心算法

### 7.1 数据清洗逻辑

参考 `workflow/03_clean_data/`，已在第 4.1.3 节说明。

### 7.2 文本预处理流程

参考 `workflow/06_preprocess_text/`，已在第 4.1.3 节说明。

### 7.3 匹配分数计算公式

#### 7.3.1 语义分计算

**TF-IDF 相似度**：
```python
from sklearn.metrics.pairwise import cosine_similarity

# 余弦相似度范围：[-1, 1]
tfidf_cosine = cosine_similarity(resume_tfidf, job_tfidf)

# 转换为 0-100 分
tfidf_score = (tfidf_cosine + 1) / 2 * 100
```

**Word2Vec 相似度**：
```python
# 文档向量：词向量平均
def doc_vector(tokens, model):
    vectors = [model.wv[word] for word in tokens if word in model.wv]
    return np.mean(vectors, axis=0) if vectors else np.zeros(100)

# 余弦相似度
w2v_cosine = cosine_similarity(resume_w2v, job_w2v)

# 转换为 0-100 分
word2vec_score = (w2v_cosine + 1) / 2 * 100
```

**语义分加权平均**：
```python
semantic_score = 0.6 * tfidf_score + 0.4 * word2vec_score
```

**权重依据**：TF-IDF 更关注关键词匹配，Word2Vec 更关注语义相似，TF-IDF 权重更高。

#### 7.3.2 规则分计算

参考 `workflow/10_calculate_rule_scores/`。

**技能匹配分（40% 权重）**：
```python
required = set(job["required_skills_standard"])
preferred = set(job["preferred_skills_standard"])
candidate = set(resume["standard_skills"])

# 必备技能匹配率
required_match_rate = len(candidate & required) / len(required) if required else 1.0

# 加分技能匹配数
preferred_match_count = len(candidate & preferred)

# 技能分 = 必备技能权重 80% + 加分技能权重 20%
skill_score = required_match_rate * 80 + min(preferred_match_count / max(len(preferred), 1), 1.0) * 20

matched_skills = list(candidate & (required | preferred))
missing_skills = list(required - candidate)
```

**学历匹配分（20% 权重）**：
```python
resume_edu_level = resume["education_level"]  # 3-6
job_edu_level = job["education_required_level"]

if resume_edu_level >= job_edu_level:
    education_score = 100
elif resume_edu_level == job_edu_level - 1:
    education_score = 70  # 差一级，扣 30 分
else:
    education_score = 0   # 差两级以上，不匹配
```

**经验匹配分（15% 权重）**：
```python
resume_exp = resume["experience_years_num"]
job_exp = job["experience_required_num"]

if resume_exp >= job_exp:
    # 经验足够，满分
    experience_score = 100
elif resume_exp >= job_exp * 0.5:
    # 经验不足但超过一半，按比例计分
    experience_score = (resume_exp / job_exp) * 100
else:
    # 经验严重不足
    experience_score = 50
```

**城市匹配分（10% 权重）**：
```python
if resume["standard_location"] == job["standard_location"]:
    city_score = 100
else:
    city_score = 0
```

**薪资匹配分（10% 权重）**：
```python
expected = resume["expected_salary"]
min_salary = job["salary_min"]
max_salary = job["salary_max"]

if min_salary <= expected <= max_salary:
    # 期望在范围内，满分
    salary_score = 100
elif expected < min_salary:
    # 期望低于范围，按差距扣分
    gap = (min_salary - expected) / min_salary
    salary_score = max(100 - gap * 50, 50)
else:
    # 期望高于范围，按差距扣分
    gap = (expected - max_salary) / max_salary
    salary_score = max(100 - gap * 100, 0)
```

**证书加分（5% 权重）**：
```python
# 简单策略：有证书就加分
if resume["certifications"] and resume["certifications"] != "无":
    certificate_score = 100
else:
    certificate_score = 0
```

**规则分加权平均**：
```python
rule_score = (
    0.40 * skill_score +
    0.20 * education_score +
    0.15 * experience_score +
    0.10 * city_score +
    0.10 * salary_score +
    0.05 * certificate_score
)
```

#### 7.3.3 总分计算

```python
total_score = 0.60 * semantic_score + 0.40 * rule_score
```

**权重设计依据**：
- 语义分 60%：文本相似度是判断"能不能做"的核心指标
- 规则分 40%：硬性条件（学历、经验、技能）是基本门槛
- 技能占规则分 40%：技能点匹配是招聘的首要考虑因素
- 学历占 20%：学历是重要但非唯一标准
- 证书占 5%：证书是加分项，不是必需项

#### 7.3.4 推荐理由生成

```python
def generate_reason(resume, job, scores, matched_skills, missing_skills):
    reasons = []
    
    # 技能匹配
    if scores["skill_score"] >= 80:
        reasons.append(f"技能匹配度高：候选人掌握 {', '.join(matched_skills[:5])} 等核心技能")
    
    # 学历匹配
    if scores["education_score"] == 100:
        reasons.append(f"学历完全符合：{resume['education']}满足岗位要求（{job['education_required']}）")
    
    # 经验匹配
    if scores["experience_score"] >= 80:
        reasons.append(f"工作经验符合：{resume['years_experience']}满足岗位要求（{job['experience_required']}）")
    
    # 城市匹配
    if scores["city_score"] == 100:
        reasons.append(f"地理位置匹配：期望城市（{resume['location']}）与岗位城市（{job['location']}）一致")
    
    # 薪资匹配
    if scores["salary_score"] >= 80:
        reasons.append(f"薪资预期合理：期望薪资 {resume['expected_salary']} 万/年在岗位范围 {job['salary_range']} 之内")
    
    # 技能缺失提示
    if missing_skills:
        reasons.append(f"需提升技能：{', '.join(missing_skills[:3])}")
    
    return "\n".join([f"{i+1}. {r}" for i, r in enumerate(reasons)])
```

---

## 8. 部署方案

### 8.1 虚拟机环境配置

**系统要求**：
- 操作系统：Ubuntu 24.04 LTS
- 内存：8GB+
- CPU：4 核+
- 磁盘：50GB+
- 网络：与宿主机网络互通

**依赖安装**：

**1. Java 环境**：
```bash
sudo apt update
sudo apt install openjdk-11-jdk -y
java -version
```

**2. Hadoop 3.3.6**（伪分布式）：
```bash
# 下载并解压
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /usr/local/hadoop

# 配置环境变量（添加到 ~/.bashrc）
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# 配置伪分布式模式（编辑 core-site.xml, hdfs-site.xml, mapred-site.xml, yarn-site.xml）
# 格式化 NameNode
hdfs namenode -format

# 启动 HDFS
start-dfs.sh

# 验证
hdfs dfs -ls /resume_matching
```

**3. Spark 3.5.1**：
```bash
# 下载并解压
wget https://dlcdn.apache.org/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz
tar -xzf spark-3.5.1-bin-hadoop3.tgz
sudo mv spark-3.5.1-bin-hadoop3 /usr/local/spark

# 配置环境变量
export SPARK_HOME=/usr/local/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# 启动 Standalone 集群
start-master.sh
start-worker.sh spark://localhost:7077

# 验证
spark-shell --version
```

**4. Python 环境**：
```bash
sudo apt install python3.10 python3-pip -y

# 安装依赖
pip3 install fastapi uvicorn pandas numpy scikit-learn gensim jieba \
    apscheduler pyspark openai websockets
```

**5. 前端环境**：
```bash
# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# 安装 nginx（用于生产部署）
sudo apt install nginx -y
```

### 8.2 服务启动脚本

#### 8.2.1 项目目录结构

```
/home/user/resume-matching/
├── data_generator/
│   ├── data_generator.py
│   ├── requirements.txt
│   └── config.json
├── streaming/
│   ├── streaming_job.py
│   ├── streaming_supervisor.sh
│   └── requirements.txt
├── batch_processing/
│   ├── batch_job.py
│   ├── batch_scheduler.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── build/  (生产构建输出)
├── scripts/
│   ├── start_all.sh
│   ├── stop_all.sh
│   └── init_hdfs.sh
└── logs/
    ├── generator.log
    ├── streaming.log
    └── batch.log
```

#### 8.2.2 HDFS 初始化脚本

**scripts/init_hdfs.sh**：
```bash
#!/bin/bash

echo "Creating HDFS directory structure..."

hdfs dfs -mkdir -p /resume_matching/raw/resumes
hdfs dfs -mkdir -p /resume_matching/raw/jobs
hdfs dfs -mkdir -p /resume_matching/processed/resumes
hdfs dfs -mkdir -p /resume_matching/processed/jobs
hdfs dfs -mkdir -p /resume_matching/models/tfidf
hdfs dfs -mkdir -p /resume_matching/models/word2vec
hdfs dfs -mkdir -p /resume_matching/output/matches
hdfs dfs -mkdir -p /resume_matching/checkpoints
hdfs dfs -mkdir -p /resume_matching/resources

echo "Uploading initial resources..."
hdfs dfs -put resources/stopwords.json /resume_matching/resources/
hdfs dfs -put resources/skill_alias.json /resume_matching/resources/

echo "HDFS initialization completed."
hdfs dfs -ls -R /resume_matching
```

#### 8.2.3 启动所有服务

**scripts/start_all.sh**：
```bash
#!/bin/bash

PROJECT_ROOT="/home/user/resume-matching"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p $LOG_DIR

echo "Starting all services..."

# 1. 启动数据生成器
echo "[1/4] Starting data generator..."
cd $PROJECT_ROOT/data_generator
nohup python3 data_generator.py > $LOG_DIR/generator.log 2>&1 &
echo $! > $LOG_DIR/generator.pid

# 2. 启动 Streaming 监督脚本
echo "[2/4] Starting Spark Streaming supervisor..."
cd $PROJECT_ROOT/streaming
nohup bash streaming_supervisor.sh > $LOG_DIR/streaming.log 2>&1 &
echo $! > $LOG_DIR/streaming.pid

# 3. 启动批处理调度器
echo "[3/4] Starting batch processing scheduler..."
cd $PROJECT_ROOT/batch_processing
nohup python3 batch_scheduler.py > $LOG_DIR/batch.log 2>&1 &
echo $! > $LOG_DIR/batch.pid

# 4. 启动前端服务
echo "[4/4] Starting frontend..."
cd $PROJECT_ROOT/frontend/build
nohup python3 -m http.server 3000 > $LOG_DIR/frontend.log 2>&1 &
echo $! > $LOG_DIR/frontend.pid

echo "All services started."
echo "View logs in $LOG_DIR"
echo ""
echo "Access URLs:"
echo "  - Frontend:         http://$(hostname -I | awk '{print $1}'):3000"
echo "  - Generator API:    http://$(hostname -I | awk '{print $1}'):8000"
echo "  - Batch API:        http://$(hostname -I | awk '{print $1}'):8001"
echo "  - Spark Master UI:  http://$(hostname -I | awk '{print $1}'):8080"
```

#### 8.2.4 停止所有服务

**scripts/stop_all.sh**：
```bash
#!/bin/bash

PROJECT_ROOT="/home/user/resume-matching"
LOG_DIR="$PROJECT_ROOT/logs"

echo "Stopping all services..."

# 读取 PID 并终止进程
for service in generator streaming batch frontend; do
    PID_FILE="$LOG_DIR/${service}.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            echo "Stopping $service (PID: $PID)..."
            kill $PID
            rm $PID_FILE
        else
            echo "$service is not running."
            rm $PID_FILE
        fi
    else
        echo "No PID file found for $service."
    fi
done

echo "All services stopped."
```

### 8.3 端口和网络配置

**端口分配**：
```
8000  - 数据生成器 FastAPI
8001  - 批处理调度器 FastAPI
3000  - React 前端
9000  - HDFS NameNode
8080  - Spark Master Web UI
4040  - Spark Application UI (动态)
50070 - HDFS Web UI (Hadoop 2.x)
9870  - HDFS Web UI (Hadoop 3.x)
```

**防火墙配置**（如果启用了 ufw）：
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 9870/tcp
```

**访问方式**：
- 从宿主机浏览器访问：`http://虚拟机IP:3000`
- 确保虚拟机网络模式为桥接或 NAT，并配置端口转发（如使用 VirtualBox/VMware）

---

## 9. 开发计划

### 9.1 里程碑划分

#### 里程碑 1：基础环境搭建

**目标**：虚拟机环境准备完成，HDFS 和 Spark 运行正常。

**任务**：
- [ ] 安装 Ubuntu 24.04，配置网络
- [ ] 安装 Hadoop 3.3.6，配置伪分布式
- [ ] 安装 Spark 3.5.1，配置 Standalone
- [ ] 测试 HDFS 读写
- [ ] 测试 Spark 任务提交
- [ ] 生成停用词表和技能标准化表
- [ ] 初始化 HDFS 目录结构

**验收标准**：
```bash
hdfs dfs -ls /resume_matching
spark-submit --version
```

#### 里程碑 2：上游数据生成服务

**目标**：数据生成器能够持续生成脏数据并写入 HDFS。

**任务**：
- [ ] 实现 `data_generator.py`：
  - [ ] OpenAI API 调用逻辑
  - [ ] 时间窗口聚合缓存
  - [ ] HDFS 写入逻辑
- [ ] 实现 FastAPI 控制接口：
  - [ ] POST /api/generator/start
  - [ ] POST /api/generator/stop
  - [ ] GET /api/generator/status
  - [ ] GET /api/generator/stats
- [ ] 测试数据生成和 HDFS 写入

**验收标准**：
- 启动生成器后，HDFS 中每分钟出现新的 CSV 文件
- 通过 API 能控制生成器启停

#### 里程碑 3：中游 Streaming 处理

**目标**：Streaming 任务能够实时清洗和处理数据。

**任务**：
- [ ] 实现 `streaming_job.py`：
  - [ ] 监听 HDFS 目录
  - [ ] 数据清洗逻辑（去重、缺失值、异常值）
  - [ ] 字段结构化逻辑（学历、经验、城市、薪资）
  - [ ] 文本预处理逻辑（分词、停用词、技能标准化）
  - [ ] 输出到 HDFS
- [ ] 配置 Checkpoint
- [ ] 实现 `streaming_supervisor.sh` 重启逻辑
- [ ] 测试 Streaming 任务

**验收标准**：
- 原始数据写入后，processed/ 目录中出现清洗后的数据
- Streaming 任务重启后能从 checkpoint 恢复

#### 里程碑 4：中游批处理任务

**目标**：批处理任务能够训练模型并生成匹配结果。

**任务**：
- [ ] 实现 `batch_job.py`：
  - [ ] TF-IDF 训练
  - [ ] Word2Vec 训练
  - [ ] 语义分计算
  - [ ] 规则分计算（6 个维度）
  - [ ] 总分计算和推荐理由生成
  - [ ] 输出匹配结果
- [ ] 实现 `batch_scheduler.py`：
  - [ ] APScheduler 配置
  - [ ] FastAPI 接口（/api/batch/trigger, /api/batch/status）
- [ ] 测试批处理任务

**验收标准**：
- 每 10 分钟自动运行批处理
- output/matches/ 中生成匹配结果 CSV
- 通过 API 能手动触发批处理

#### 里程碑 5：下游 Web 前端

**目标**：React 前端能够展示系统状态和匹配结果。

**任务**：
- [ ] 项目初始化（React + Ant Design + Zustand）
- [ ] 实现模块 A：系统监控面板
  - [ ] WebSocket 连接
  - [ ] 实时状态显示
- [ ] 实现模块 B：数据生成器控制
  - [ ] 启动/停止按钮
  - [ ] 配置面板
- [ ] 实现模块 C：岗位匹配查询
  - [ ] 岗位列表
  - [ ] 简历列表
  - [ ] 筛选和搜索
- [ ] 实现模块 D：简历推荐查询
- [ ] 实现模块 E：匹配详情页
  - [ ] 分数详情展示
  - [ ] 推荐理由展示
- [ ] 生产构建（npm run build）

**验收标准**：
- 前端能够访问并显示实时数据
- 所有功能模块正常工作

#### 里程碑 6：下游 Web 后端 API

**目标**：FastAPI 后端提供前端所需的所有数据接口。

**任务**：
- [ ] 实现 WebSocket 接口（/ws/status）
- [ ] 实现业务数据接口：
  - [ ] GET /api/jobs
  - [ ] GET /api/jobs/{job_id}/matches
  - [ ] GET /api/resumes
  - [ ] GET /api/resumes/{resume_id}/recommendations
  - [ ] GET /api/matches/{resume_id}/{job_id}
- [ ] HDFS 数据读取逻辑
- [ ] 数据缓存策略（避免频繁读取 HDFS）

**验收标准**：
- 所有 API 接口返回正确数据
- WebSocket 实时推送系统状态

#### 里程碑 7：集成测试和部署（2-3 天）

**目标**：完整系统在虚拟机上运行正常。

**任务**：
- [ ] 编写启动/停止脚本
- [ ] 端到端测试：数据生成 → 处理 → 展示
- [ ] 压力测试：大量数据场景
- [ ] 日志和错误处理优化
- [ ] 编写部署文档和用户手册
- [ ] 准备演示 Demo

**验收标准**：
- 一键启动所有服务
- 系统稳定运行 1 小时以上
- 前端能够看到数据流动和匹配结果

### 9.2 优先级排序

**P0（必须完成）**：
- 里程碑 1, 2, 3, 4, 5, 6, 7 的所有核心功能
- 数据生成 → Streaming 清洗 → 批处理匹配 → Web 展示的完整链路

**P1（重要但可延后）**：
- 批处理任务的手动触发接口
- 数据生成器的配置调整接口
- 匹配详情页的高级可视化（图表）

**P2（锦上添花）**：
- 数据浏览功能（查看 HDFS 原始数据）
- 系统日志查看功能
- 模型性能指标展示（训练时间、准确率）

---

## 10. 附录

### 10.1 参考文档

- 参考项目：`/Users/yem/.hermes/profiles/lark-hermes/workspace/resume-matching/reference/workflow`
- 学生项目任务书：`学生项目任务书：基于大数据+AI的简历-岗位人才匹配系统.md`
- Hadoop 官方文档：https://hadoop.apache.org/docs/r3.3.6/
- Spark 官方文档：https://spark.apache.org/docs/3.5.1/
- FastAPI 文档：https://fastapi.tiangolo.com/
- React 文档：https://react.dev/

### 10.2 术语表

| 术语 | 说明 |
|-----|------|
| 上游 | 数据生成层，负责产生原始数据 |
| 中游 | 数据处理层，包括 Streaming 和批处理 |
| 下游 | 数据展示层，Web 前端和后端 API |
| 脏数据 | 包含质量问题的原始数据（缺失值、重复、格式不统一） |
| 时间窗口聚合 | 将一段时间内的数据合并成一个文件 |
| Checkpoint | Spark Streaming 的容错机制，保存处理状态 |
| 语义分 | 基于文本相似度的匹配分数（TF-IDF + Word2Vec） |
| 规则分 | 基于硬性条件的匹配分数（技能、学历、经验等） |
| 笛卡尔积 | 简历×岗位的所有可能组合 |
| 伪分布式 | 单机模拟分布式环境的 Hadoop 部署模式 |

---

**PRD 文档结束**

**版本历史**：
- v1.0 (2026-06-09): 初始版本，完整架构设计和开发计划
