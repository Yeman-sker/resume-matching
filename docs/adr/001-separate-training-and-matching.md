# ADR-001: 分离模型训练和匹配计算

## 状态

提议（Proposed）

## 背景

当前批处理任务每 10 分钟运行一次，每次都执行以下操作：

1. 读取 HDFS 全部清洗后数据
2. 训练 TF-IDF 和 Word2Vec 模型
3. 计算简历×岗位笛卡尔积匹配分数
4. 保存匹配结果和模型

### 存在的问题

1. **重复训练浪费算力**：每次都重新训练模型，已处理过的数据被重复计算
2. **数据量持续增长**：
   - 上游每 60 秒生成 20 条数据
   - 10 小时后：6000 简历 × 6000 岗位 = 3600 万条匹配记录
   - 笛卡尔积计算复杂度 O(n²)，无法持续运行
3. **模型不稳定**：Word2Vec 有随机性，每次训练结果略有差异，匹配分数波动

### 为什么不能增量训练？

TF-IDF 和 Word2Vec 是**全局统计模型**，需要全量数据才能保证分数公平：

**TF-IDF 问题**：
```
批次 1（1000 条）: IDF("Python") = log(1000/800) = 0.22
批次 2（1000 条）: IDF("Python") = log(1000/850) = 0.16

问题：相同内容的简历在不同批次得分不同，不公平
```

**Word2Vec 问题**：
```
批次 1 只见过 Python 相关词汇
批次 2 只见过 Java 相关词汇

问题：无法建立跨批次的词语关系
```

## 决策

采用**分离训练和匹配**架构：

### 1. 模型训练任务（低频，全量）

- **频率**：每天凌晨 3 点运行一次
- **数据**：读取全部历史数据（可选：滑动窗口，如最近 30 天）
- **输出**：带日期版本的 MLlib 模型目录（如 `tfidf_v20260611/`）
- **存储**：保存到 HDFS `/resume_matching/models/`

### 2. 匹配计算任务（高频，增量）

- **频率**：每 10 分钟运行一次
- **数据**：只读取上次运行后的新增简历/岗位
- **模型**：加载最新训练的模型（不重新训练）
- **输出**：增量匹配结果追加到 HDFS

### 3. 数据窗口策略

引入滑动窗口限制数据量：

- 只保留最近 30 天的数据参与训练
- 超过 30 天的数据归档到 `/resume_matching/archived/`
- 定期清理归档数据

## 实现方案

### 目录结构调整

```
batch_processing/
├── train_models.py          # 模型训练任务（每日）
├── match_incremental.py     # 增量匹配任务（每 10 分钟）
├── scheduler_train.py       # 训练任务调度器
├── scheduler_match.py       # 匹配任务调度器
└── utils/
    ├── model_loader.py      # 模型加载工具
    └── checkpoint.py        # 记录上次处理位置
```

### 核心代码逻辑

**训练任务** (`train_models.py`):

```python
def train_models_daily():
    # 读取最近 30 天的数据
    cutoff = datetime.now() - timedelta(days=30)
    resumes = spark.read.csv(...).filter(col("create_time") > cutoff)
    jobs = spark.read.csv(...).filter(col("create_time") > cutoff)

    # 使用 Spark MLlib 训练模型
    cv_model = CountVectorizer(
        inputCol="tokens",
        outputCol="raw_features",
        vocabSize=500,
        minDF=2,
    ).fit(train_df)
    idf_model = IDF(
        inputCol="raw_features",
        outputCol="tfidf_features",
    ).fit(cv_model.transform(train_df))
    w2v_model = Word2Vec(
        inputCol="tokens",
        outputCol="w2v_vector",
        vectorSize=100,
    ).fit(train_df)

    # 保存带日期版本的模型
    version = datetime.now().strftime("%Y%m%d")
    cv_model.save(f"{HDFS_BASE}/models/count_vectorizer/cv_v{version}")
    idf_model.save(f"{HDFS_BASE}/models/tfidf/tfidf_v{version}")
    w2v_model.save(f"{HDFS_BASE}/models/word2vec/w2v_v{version}")
```

**匹配任务** (`match_incremental.py`):

```python
def match_incremental():
    # 加载最新模型（不重新训练）
    tfidf = load_latest_model("tfidf")
    w2v = load_latest_model("word2vec")

    # 读取 checkpoint 记录的上次处理时间
    last_run = load_checkpoint()
    new_resumes = spark.read.csv(...).filter(col("create_time") > last_run)

    # 只为新简历计算匹配（全量岗位）
    all_jobs = spark.read.csv(f"{HDFS_BASE}/processed/jobs")
    results = calculate_matches(new_resumes, all_jobs, tfidf, w2v)

    # 保存结果并更新 checkpoint
    save_results(results)
    save_checkpoint(datetime.now())
```

### Checkpoint 机制

新增 checkpoint 文件记录上次处理位置：

```
/resume_matching/checkpoints/match_incremental/
└── last_run.json
    {
      "timestamp": "2026-06-11T14:30:00",
      "processed_resumes": 1523,
      "processed_jobs": 456
    }
```

## 影响

### 优点

1. **节约算力**：模型每天只训练一次，减少 95% 的训练计算量
2. **保证公平**：所有数据使用同一模型，分数可比
3. **匹配实时性**：匹配任务仍然每 10 分钟运行，响应及时
4. **数据量可控**：滑动窗口限制训练数据量，避免 OOM
5. **模型稳定**：模型一天只变化一次，分数波动小

### 缺点

1. **延迟**：新数据最多延迟 24 小时才能影响模型（可通过缩短训练周期缓解）
2. **实现复杂度**：需要拆分为两个独立任务，增加 checkpoint 管理
3. **模型时效性**：如果数据分布快速变化，模型可能滞后

### 权衡

- 牺牲了模型的实时性（延迟最多 24 小时）
- 换取了计算效率（减少 95% 训练计算）和分数公平性
- 对教学和大多数生产场景，这个权衡是值得的

## 实施计划

### 阶段 1：最小可行实现（MVP）

1. 拆分 `batch_job.py` 为 `train_models.py` 和 `match_incremental.py`
2. 实现模型加载工具 `model_loader.py`
3. 实现 checkpoint 机制 `checkpoint.py`
4. 修改调度器，分别调度两个任务

### 阶段 2：数据窗口优化

1. 实现 30 天滑动窗口过滤
2. 实现数据归档脚本
3. 定期清理归档数据

### 阶段 3：监控和告警

1. 添加模型训练成功/失败监控
2. 添加匹配任务延迟监控
3. 添加数据量增长告警
---

**日期**: 2026-06-11  
**作者**: Claude (教学项目)  
**审核者**: 待定
