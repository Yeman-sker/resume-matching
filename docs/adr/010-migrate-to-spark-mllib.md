# ADR-010: 使用 Spark MLlib 实现 TF-IDF 和 Word2Vec

## 状态

已接受（Accepted）

## 背景

当前 `batch_job.py` 使用 scikit-learn 和 gensim 实现 TF-IDF 和 Word2Vec：

```python
# 当前实现
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models import Word2Vec

# 需要先 collect 到 driver
resumes = resumes_df.collect()
jobs = jobs_df.collect()

# 在 driver 内存中训练
tfidf = TfidfVectorizer(max_features=500).fit(all_texts)
w2v = Word2Vec(...).fit(all_tokens)

# Python 循环计算笛卡尔积匹配
for resume in resumes:
    for job in jobs:
        score = calculate_match(resume, job, tfidf, w2v)
```

### 存在的问题

1. **内存瓶颈**：所有数据 collect 到 driver，数据量增长后容易 OOM
2. **单机计算**：训练和匹配都在 driver 单线程执行，无法利用集群资源
3. **技术栈混杂**：Spark + scikit-learn + gensim 三套工具，依赖管理复杂
4. **笛卡尔积性能差**：Python 双层循环计算 O(n²) 匹配，无法并行

**数据量增长示例：**
- 当前：1000 简历 × 1000 岗位 = 100 万条匹配记录（可接受）
- 10 小时后：6000 × 6000 = 3600 万条（Python 循环无法完成）

## 决策

**完全迁移到 Spark MLlib，全程 Spark 化处理。**

### 实现方案

**1. TF-IDF 实现：CountVectorizer + IDF**

```python
from pyspark.ml.feature import CountVectorizer, IDF

# 构建词表（最多 500 词，至少在 2 个文档出现）
cv = CountVectorizer(inputCol="tokens", outputCol="raw_features", 
                     vocabSize=500, minDF=2)
cv_model = cv.fit(train_df)

# 计算 IDF
idf = IDF(inputCol="raw_features", outputCol="tfidf_features")
idf_model = idf.fit(cv_model.transform(train_df))
```

**为什么不用 HashingTF？**
- HashingTF 用哈希函数映射词到固定维度，存在哈希冲突
- CountVectorizer 构建精确词表，匹配精度更高
- 500 维词表内存占用可接受

**2. Word2Vec 实现：MLlib Word2Vec**

```python
from pyspark.ml.feature import Word2Vec

w2v = Word2Vec(inputCol="tokens", outputCol="w2v_vector",
               vectorSize=100, windowSize=5, minCount=1, 
               maxIter=30, seed=42)
w2v_model = w2v.fit(train_df)
```

**参数对应关系：**
| gensim 参数 | MLlib 参数 | 值 |
|------------|-----------|-----|
| vector_size | vectorSize | 100 |
| window | windowSize | 5 |
| min_count | minCount | 1 |
| epochs | maxIter | 30 |
| seed | seed | 42 |
| workers | (自动并行) | - |

**3. 分布式匹配计算：crossJoin + UDF**

```python
# 列重命名避免冲突
resumes = resumes.select([col(c).alias(f"resume_{c}") for c in resumes.columns])
jobs = jobs.select([col(c).alias(f"job_{c}") for c in jobs.columns])

# 笛卡尔积（分布式并行）
matches = resumes.crossJoin(jobs)

# 计算余弦相似度（独立 UDF）
@udf(returnType=DoubleType())
def cosine_sim_udf(v1, v2):
    if v1 is None or v2 is None:
        return 0.0
    dot = float(v1.dot(v2))
    norm = float(v1.norm(2) * v2.norm(2))
    return dot / norm if norm > 0 else 0.0

matches = matches.withColumn("tfidf_sim", cosine_sim_udf(...))
matches = matches.withColumn("w2v_sim", cosine_sim_udf(...))

# 计算所有维度分数（主 UDF）
@udf(returnType=score_schema)
def calc_all_scores(resume_struct, job_struct, tfidf_sim, w2v_sim):
    # 语义分
    semantic_score = (tfidf_sim * 0.6 + w2v_sim * 0.4) * 100
    # 规则分（技能、学历、经验等）
    skill_score = score_skill(...)
    # ... 其他维度
    return {...}

matches = matches.withColumn("scores", calc_all_scores(...))
```

**4. 数据预处理**

**tokens 列转换：**
```python
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import ArrayType, StringType

# 从 JSON 字符串转为 Array[String]
df = df.withColumn("tokens", from_json(col("tokens"), ArrayType(StringType())))
```

**技能列转换：**
```python
from pyspark.sql.functions import split, array_remove

# 从管道符分隔字符串转为 Array[String]，并清理空值
df = df.withColumn(
    "standard_skills_array",
    array_remove(split(col("standard_skills"), "\\|"), "")
)
```

**空值处理策略：**
- **训练时**：过滤掉 tokens 为空的记录（`filter(size(col("tokens")) > 0)`）
- **匹配时**：保留所有记录，空向量的相似度返回 0，依靠其他维度评分

**5. 模型保存**

```python
# 直接保存到 HDFS（目录格式）
cv_model.save(f"{HDFS_BASE}/models/count_vectorizer/cv_v{version}")
idf_model.save(f"{HDFS_BASE}/models/tfidf/tfidf_v{version}")
w2v_model.save(f"{HDFS_BASE}/models/word2vec/w2v_v{version}")

# 加载
from pyspark.ml.feature import CountVectorizerModel, IDFModel, Word2VecModel
cv_model = CountVectorizerModel.load(path)
idf_model = IDFModel.load(path)
w2v_model = Word2VecModel.load(path)
```

**注意：** MLlib 模型保存为目录结构（包含 metadata/ 和 data/），不是单个文件。

## 影响

### 优点

1. **可扩展性**：分布式训练和计算，支持数据量增长到百万级
2. **性能提升**：crossJoin + UDF 利用集群并行，比 Python 循环快数十倍
3. **技术栈统一**：全部用 PySpark，简化依赖和部署
4. **避免 OOM**：不需要 collect 到 driver，内存压力分散到集群

### 缺点

1. **代码复杂度**：需要理解 MLlib API 和 Spark DataFrame 操作
2. **调试难度**：UDF 报错信息不如 Python 循环直观
3. **小数据量性能**：数据量很小时（<100 条），Spark 调度开销反而更慢

### 权衡

- 牺牲了小数据量场景的性能（Spark 调度开销）
- 换取了大数据量场景的可扩展性和性能
- 对教学项目和真实生产场景，这个权衡是值得的

## 实施计划

### 阶段 1：替换模型训练（本次）

1. 用 `CountVectorizer + IDF` 替换 `TfidfVectorizer`
2. 用 MLlib `Word2Vec` 替换 gensim `Word2Vec`
3. 实现数据预处理（tokens 和技能列转换）
4. 模型保存改为直接写 HDFS

### 阶段 2：替换匹配计算（本次）

1. 实现余弦相似度 UDF
2. 实现主评分 UDF（7 个维度 + matched_skills + missing_skills + reason）
3. 用 crossJoin + UDF 替换 Python 双层循环
4. 验证匹配结果与原实现一致

### 阶段 3：性能测试和优化

1. 对比迁移前后的执行时间
2. 测试不同数据量下的表现（1k、10k、100k）
3. 调优 Spark 参数（分区数、executor 内存等）

## 后续考虑

### 与 ADR-001 的关系

本 ADR 是在当前一体式任务（`batch_job.py`）中替换实现，不涉及架构拆分。

ADR-001（分离训练和匹配）仍然是独立的架构决策，可以在本次迁移后实施：
- 训练任务：用 MLlib 每日全量训练
- 匹配任务：用 MLlib 增量计算匹配

两个决策互不冲突，本次迁移为未来拆分打好技术基础。

### 增量训练的可能性

MLlib 的 CountVectorizer 和 Word2Vec 也不支持增量训练（需要全量 fit），这进一步印证了 ADR-001 的合理性：
- 模型训练应该低频全量（如每日一次）
- 匹配计算应该高频增量（如每 10 分钟）

---

**日期**：2026-06-11  
**作者**：Claude Code（教学项目）  
**审核者**：待定
