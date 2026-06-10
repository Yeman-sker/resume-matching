# 中游批处理任务

## 功能

- 每 10 分钟自动运行一次（APScheduler）
- 训练 TF-IDF 和 Word2Vec 模型
- 计算语义分数（TF-IDF 60% + Word2Vec 40%）
- 计算规则分数（技能 40% + 学历 20% + 经验 15% + 城市 10% + 薪资 10% + 证书 5%）
- 生成简历×岗位笛卡尔积匹配结果

## 安装

```bash
cd batch_processing
pip3 install -r requirements.txt
```

## 运行

### 启动调度器

```bash
python3 batch_scheduler.py
```

调度器会：
1. 立即运行一次批处理任务
2. 每 10 分钟自动触发一次

### 手动运行单次任务

```bash
spark-submit --master local[*] --driver-memory 4g batch_job.py
```

## 匹配算法

### 总分公式

```
总分 = 语义分 × 0.60 + 规则分 × 0.40
```

### 语义分

```
语义分 = TF-IDF 分 × 0.6 + Word2Vec 分 × 0.4
```

- **TF-IDF**：基于词频-逆文档频率的文本相似度
- **Word2Vec**：基于词向量的语义相似度

### 规则分

```
规则分 = 技能分×0.40 + 学历分×0.20 + 经验分×0.15 + 城市分×0.10 + 薪资分×0.10 + 证书分×0.05
```

#### 技能匹配
- 计算简历技能与岗位要求的交集比例
- 分数 = (共同技能数 / 岗位要求技能数) × 100

#### 学历匹配
- 学历等级：大专(1) < 本科(2) < 硕士(3) < 博士(4)
- 满足要求：100 分
- 每低一级：扣 20 分

#### 经验匹配
- 满足要求：100 分
- 每少一年：扣 15 分

#### 城市匹配
- 完全匹配：100 分
- 不匹配：0 分

#### 薪资匹配
- 基于期望薪资和岗位薪资的平均值差异
- 分数 = max(0, 100 - 差异比例 × 50)

#### 证书匹配
- 计算简历证书与岗位要求的交集比例
- 分数 = (匹配证书数 / 要求证书数) × 100

## 输出

### 匹配结果
- **位置**：`hdfs://localhost:9000/resume_matching/output/matches/*.csv`
- **字段**：
  - resume_id, job_id
  - total_score（总分）
  - semantic_score（语义分）
  - rule_score（规则分）
  - skill_score, education_score, experience_score, city_score, salary_score, certificate_score

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
