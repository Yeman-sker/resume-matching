# 中游批处理任务

## 功能

- 每 10 分钟自动运行一次（APScheduler）
- 训练 TF-IDF 和 Word2Vec 模型
- 计算语义分数（TF-IDF 60% + Word2Vec 40%）
- 计算技能、学历、经验、城市、薪资和证书分
- 生成简历×岗位笛卡尔积匹配结果

## 安装

```bash
bash scripts/setup_python_env.sh
```

## 运行

### 启动调度器

```bash
bash batch_processing/start.sh
```

调度器会：
1. 立即运行一次批处理任务
2. 每 10 分钟自动触发一次

### 手动运行单次任务

```bash
export PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"
export PYSPARK_PYTHON="$PWD/.venv/bin/python"
spark-submit --master local[*] --driver-memory 4g batch_processing/batch_job.py
```

## 匹配算法

### 总分公式

```
总分 = 技能分×0.30 + 语义分×0.30 + 学历分×0.15
     + 经验分×0.10 + 城市分×0.05 + 薪资分×0.05 + 证书分×0.05
```

### 语义分

```
语义分 = TF-IDF 分 × 0.6 + Word2Vec 分 × 0.4
```

- **TF-IDF**：基于词频-逆文档频率的文本相似度
- **Word2Vec**：基于词向量的语义相似度

#### 技能匹配
- 必备技能最多 85 分
- 加分技能每命中一个加 5 分，最多 15 分

#### 学历匹配
- 学历等级：高中(1) < 大专(2) < 本科(3) < 硕士(4) < 博士(5)
- 满足要求：100 分
- 低一级：60 分；差距更大：30 分

#### 经验匹配
- 满足要求：100 分
- 少一年：70 分；少两年：40 分；差距更大：20 分

#### 城市匹配
- 完全匹配：100 分；未知：60 分；不匹配：50 分

#### 薪资匹配
- 岗位年薪上限达到期望：100 分
- 达到期望的 80%：70 分；否则 40 分；未知：60 分

#### 证书匹配
- 简历有证书：100 分
- 简历无证书：60 分

## 输出

### 匹配结果
- **位置**：`hdfs://localhost:9000/resume_matching/output/matches/*.csv`
- **字段**：
  - resume_id, resume_name, job_id, job_title, department
  - tfidf_score, word2vec_score, semantic_score, total_score
  - skill_score, education_score, experience_score, city_score, salary_score, certificate_score
  - matched_skills, missing_skills, reason

### 训练模型
- **TF-IDF**：`hdfs://localhost:9000/resume_matching/models/tfidf/tfidf_vYYYYMMDDHHMM.pkl`
- **Word2Vec**：`hdfs://localhost:9000/resume_matching/models/word2vec/word2vec_vYYYYMMDDHHMM.model`

## 数据流

```
HDFS processed/resumes/*.csv
  +
HDFS processed/jobs/*.csv
  ↓ [训练模型 + 计算匹配分]
HDFS output/matches/match_results.csv
HDFS models/tfidf/*.pkl
HDFS models/word2vec/*.model
```

## 性能

- **数据规模**：100 简历 × 100 岗位 = 10,000 条匹配记录
- **执行时间**：约 2-5 分钟（取决于数据量）
- **内存需求**：Driver 4GB

## 停止

```bash
# Ctrl+C 停止调度器
# 或
pkill -f batch_scheduler.py
```
