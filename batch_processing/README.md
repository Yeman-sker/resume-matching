# 中游批处理任务

## 功能

- 每 10 分钟自动运行一次（APScheduler）
- 训练 TF-IDF 和 Word2Vec 模型
- 计算语义分数（TF-IDF 60% + Word2Vec 40%）
- 计算规则分数（技能、学历、经验、城市、薪资、证书）
- 生成简历×岗位笛卡尔积匹配结果
- 生成推荐理由

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
cd batch_processing
spark-submit --master local[*] --driver-memory 4g batch_job.py
```

## 匹配算法

### 总分公式

```
总分 = 技能分×0.30 + 语义分×0.30 + 学历分×0.15
     + 经验分×0.10 + 城市分×0.05 + 薪资分×0.05 + 证书分×0.05
```

### 语义分计算

```
语义分 = TF-IDF 分×0.60 + Word2Vec 分×0.40
```

- **TF-IDF**：基于词频-逆文档频率的文本相似度（max_features=500）
- **Word2Vec**：基于词向量的语义相似度（vector_size=100, window=5, epochs=30）
- **余弦相似度转换**：`(cosine_similarity + 1) / 2 * 100` 映射到 0-100 分

### 各维度评分规则

#### 技能匹配（30% 权重）
- 必备技能匹配率 × 85 + 加分技能匹配个数 × 5（最多+15）
- 返回共同技能和缺失技能

#### 学历匹配（15% 权重）
- 学历等级：未知(0) < 高中(1) < 大专(2) < 本科(3) < 硕士(4) < 博士(5)
- 满足要求：100 分
- 差 1 级：60 分
- 差 2 级及以上：30 分

#### 经验匹配（10% 权重）
- 满足要求：100 分
- 差 1 年：70 分
- 差 2 年：40 分
- 差 3 年及以上：20 分

#### 城市匹配（5% 权重）
- 城市匹配：100 分
- 城市不匹配：50 分
- 城市未知：60 分

#### 薪资匹配（5% 权重）
- 期望薪资 ≤ 岗位上限：100 分
- 岗位上限 ≥ 期望薪资 × 0.8：70 分
- 其他：40 分
- 薪资未知：60 分

#### 证书匹配（5% 权重）
- 有证书：100 分
- 无证书：60 分

## 输出

### 匹配结果
- **位置**：`hdfs://localhost:9000/resume_matching/output/matches/*.csv`
- **写入模式**：overwrite（每次覆盖）
- **字段**：
  - resume_id, resume_name, job_id, job_title, department
  - tfidf_score, word2vec_score, semantic_score
  - skill_score, education_score, experience_score, city_score, salary_score, certificate_score
  - total_score
  - matched_skills, missing_skills（管道符分隔）
  - reason（推荐理由文本）

### 训练模型
- **TF-IDF**：`hdfs://localhost:9000/resume_matching/models/tfidf/tfidf_v202406111530.pkl`
- **Word2Vec**：`hdfs://localhost:9000/resume_matching/models/word2vec/word2vec_v202406111530.model`
- **版本号格式**：`YYYYMMDDHHmm`（精确到分钟）

## 数据流

```
HDFS processed/resumes/*.csv
  +
HDFS processed/jobs/*.csv
  ↓ [训练模型 + 计算语义分 + 计算规则分]
HDFS output/matches/*.csv (匹配结果)
HDFS models/tfidf/*.pkl (TF-IDF 模型)
HDFS models/word2vec/*.model (Word2Vec 模型)
```

## 性能

- **数据规模**：100 简历 × 100 岗位 = 10,000 条匹配记录
- **执行时间**：约 2-5 分钟（取决于数据量）
- **内存需求**：Driver 4GB, Executor 4GB

## 停止

```bash
# Ctrl+C 停止调度器
# 或
pkill -f batch_scheduler.py
```
