from datetime import datetime

from pyspark.ml.feature import CountVectorizer, IDF, Word2Vec
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    array_remove,
    col,
    from_json,
    lit,
    size,
    split,
    struct,
    udf,
    when,
)
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)

spark = (
    SparkSession.builder.appName("BatchMatching")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

HDFS_BASE = "hdfs://localhost:9000/resume_matching"
MODEL_VERSION = datetime.now().strftime("%Y%m%d%H%M")
SCORE_WEIGHTS = {
    "skill": 0.30,
    "semantic": 0.30,
    "education": 0.15,
    "experience": 0.10,
    "city": 0.05,
    "salary": 0.05,
    "certificate": 0.05,
}


# 余弦相似度 UDF
@udf(returnType=DoubleType())
def cosine_sim_udf(v1, v2):
    if v1 is None or v2 is None:
        return 0.0
    dot = float(v1.dot(v2))
    norm_product = float(v1.norm(2) * v2.norm(2))
    if norm_product == 0:
        return 0.0
    similarity = dot / norm_product
    # 转换为 0-100 分数
    return max(0.0, min(100.0, (similarity + 1) / 2 * 100))


# 评分函数（纯 Python，供 UDF 调用）
def score_skill(resume_skills, required_skills, preferred_skills):
    resume_set = set(s for s in resume_skills if s)
    required_set = set(s for s in required_skills if s)
    preferred_set = set(s for s in preferred_skills if s)

    if not required_set:
        return 60.0, set(), set()
    matched = resume_set & required_set
    missing = required_set - resume_set
    required_score = len(matched) / len(required_set) * 85
    preferred_bonus = min(len(resume_set & preferred_set) * 5, 15)
    return min(required_score + preferred_bonus, 100.0), matched, missing


def score_education(resume_level, required_level):
    if required_level == 0 or resume_level >= required_level:
        return 100.0
    return 60.0 if required_level - resume_level == 1 else 30.0


def score_experience(resume_years, required_years):
    if resume_years >= required_years:
        return 100.0
    gap = required_years - resume_years
    if gap == 1:
        return 70.0
    if gap == 2:
        return 40.0
    return 20.0


def score_city(resume_city, job_city):
    if resume_city == "未知" or job_city == "未知":
        return 60.0
    return 100.0 if resume_city == job_city else 50.0


def score_salary(expected_salary, salary_max):
    if expected_salary <= 0 or salary_max <= 0:
        return 60.0
    if salary_max >= expected_salary:
        return 100.0
    return 70.0 if salary_max / expected_salary >= 0.8 else 40.0


def score_certificate(certifications):
    cert_list = [c for c in certifications if c]
    return 100.0 if cert_list else 60.0


def display_skills(skills):
    return "、".join(sorted(skills)) if skills else "无"


def build_reason(scores, matched, missing):
    reasons = []
    if scores["skill_score"] >= 80:
        reasons.append(f"技能匹配较高，共同技能包括：{display_skills(matched)}")
    elif scores["skill_score"] >= 50:
        reasons.append(f"技能部分匹配，共同技能包括：{display_skills(matched)}")
    else:
        reasons.append("技能匹配偏低，需要补充岗位核心技能")
    if missing:
        reasons.append(f"仍缺少技能：{display_skills(missing)}")

    if scores["semantic_score"] >= 80:
        reasons.append("简历文本与岗位描述方向非常接近")
    elif scores["semantic_score"] >= 50:
        reasons.append("简历文本与岗位描述存在一定相关性")
    else:
        reasons.append("文本相似度较低")

    reasons.append(
        "学历满足要求" if scores["education_score"] == 100 else "学历与岗位要求存在差距"
    )
    if scores["experience_score"] == 100:
        reasons.append("经验年限满足岗位要求")
    elif scores["experience_score"] >= 70:
        reasons.append("经验略低于要求，但差距不大")
    else:
        reasons.append("经验年限与岗位要求差距较大")
    reasons.append("城市匹配" if scores["city_score"] == 100 else "城市不完全匹配")
    return "；".join(reasons)


# 主评分 UDF Schema
score_schema = StructType(
    [
        StructField("tfidf_score", DoubleType(), False),
        StructField("word2vec_score", DoubleType(), False),
        StructField("semantic_score", DoubleType(), False),
        StructField("skill_score", DoubleType(), False),
        StructField("education_score", DoubleType(), False),
        StructField("experience_score", DoubleType(), False),
        StructField("city_score", DoubleType(), False),
        StructField("salary_score", DoubleType(), False),
        StructField("certificate_score", DoubleType(), False),
        StructField("total_score", DoubleType(), False),
        StructField("matched_skills", StringType(), False),
        StructField("missing_skills", StringType(), False),
        StructField("reason", StringType(), False),
    ]
)


# 主评分 UDF
@udf(returnType=score_schema)
def calc_all_scores_udf(resume, job, tfidf_sim, w2v_sim):
    # 语义分
    semantic_score = tfidf_sim * 0.6 + w2v_sim * 0.4

    # 技能分
    skill_score, matched, missing = score_skill(
        resume.standard_skills_array or [],
        job.required_skills_standard_array or [],
        job.preferred_skills_standard_array or [],
    )

    # 其他维度分数
    education_score = score_education(
        int(resume.education_level or 0), int(job.education_required_level or 0)
    )
    experience_score = score_experience(
        int(resume.experience_years_num or 0), int(job.experience_required_num or 0)
    )
    city_score = score_city(
        str(resume.standard_location or "未知"), str(job.standard_location or "未知")
    )
    salary_score = score_salary(
        int(resume.expected_salary or 0), int(job.salary_max or 0)
    )
    certificate_score = score_certificate(resume.certification_items_array or [])

    # 总分
    scores_dict = {
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "education_score": education_score,
        "experience_score": experience_score,
        "city_score": city_score,
        "salary_score": salary_score,
        "certificate_score": certificate_score,
    }
    total_score = sum(
        scores_dict[name + "_score"] * weight for name, weight in SCORE_WEIGHTS.items()
    )

    # 推荐理由
    reason = build_reason(scores_dict, matched, missing)

    return (
        round(tfidf_sim, 4),
        round(w2v_sim, 4),
        round(semantic_score, 4),
        round(skill_score, 4),
        round(education_score, 4),
        round(experience_score, 4),
        round(city_score, 4),
        round(salary_score, 4),
        round(certificate_score, 4),
        round(total_score, 4),
        "|".join(sorted(matched)),
        "|".join(sorted(missing)),
        reason,
    )



print(f"[{datetime.now()}] 开始批处理任务...")
print("[1/6] 读取和预处理数据...")
resumes_df = spark.read.csv(
    f"{HDFS_BASE}/processed/resumes", header=True, inferSchema=True
)
jobs_df = spark.read.csv(f"{HDFS_BASE}/processed/jobs", header=True, inferSchema=True)

# 转换 tokens 列（JSON 字符串 -> Array[String]）
resumes_df = resumes_df.withColumn(
    "tokens", from_json(col("tokens"), ArrayType(StringType()))
)
jobs_df = jobs_df.withColumn("tokens", from_json(col("tokens"), ArrayType(StringType())))

# 转换技能列（管道符分隔 -> Array[String]，清理空值）
for skill_col in ["standard_skills"]:
    resumes_df = resumes_df.withColumn(
        f"{skill_col}_array", array_remove(split(col(skill_col), "\\|"), "")
    )

for skill_col in ["required_skills_standard", "preferred_skills_standard"]:
    jobs_df = jobs_df.withColumn(
        f"{skill_col}_array", array_remove(split(col(skill_col), "\\|"), "")
    )

# 转换证书列
resumes_df = resumes_df.withColumn(
    "certification_items_array",
    array_remove(split(col("certification_items"), "\\|"), ""),
)

# 处理空 tokens（训练时过滤，匹配时保留）
resumes_df = resumes_df.withColumn(
    "tokens",
    when(col("tokens").isNull() | (size(col("tokens")) == 0), None).otherwise(
        col("tokens")
    ),
)
jobs_df = jobs_df.withColumn(
    "tokens",
    when(col("tokens").isNull() | (size(col("tokens")) == 0), None).otherwise(
        col("tokens")
    ),
)

resume_count = resumes_df.count()
job_count = jobs_df.count()
print(f"  简历数: {resume_count}, 岗位数: {job_count}")

if resume_count == 0 or job_count == 0:
    print("数据不足，跳过本次任务")
    spark.stop()
    raise SystemExit(0)


print("[2/6] 训练 TF-IDF 模型...")
# 合并简历和岗位数据用于训练（过滤空 tokens）
train_df = resumes_df.select("tokens").union(jobs_df.select("tokens"))
train_df = train_df.filter(col("tokens").isNotNull() & (size(col("tokens")) > 0))

# CountVectorizer：构建词表
cv = CountVectorizer(
    inputCol="tokens", outputCol="raw_features", vocabSize=500, minDF=2
)
cv_model = cv.fit(train_df)

# IDF：计算逆文档频率
idf = IDF(inputCol="raw_features", outputCol="tfidf_features")
idf_model = idf.fit(cv_model.transform(train_df))

print("[3/6] 训练 Word2Vec 模型...")
w2v = Word2Vec(
    inputCol="tokens",
    outputCol="w2v_vector",
    vectorSize=100,
    windowSize=5,
    minCount=1,
    maxIter=30,
    seed=42,
)
w2v_model = w2v.fit(train_df)


print("[4/6] 生成 TF-IDF 和 Word2Vec 向量...")
# 转换简历
resumes_with_cv = cv_model.transform(resumes_df)
resumes_with_tfidf = idf_model.transform(resumes_with_cv)
resumes_with_w2v = w2v_model.transform(resumes_with_tfidf)

# 转换岗位
jobs_with_cv = cv_model.transform(jobs_df)
jobs_with_tfidf = idf_model.transform(jobs_with_cv)
jobs_with_w2v = w2v_model.transform(jobs_with_tfidf)

# 重命名列避免 crossJoin 冲突
resume_cols = resumes_with_w2v.columns
job_cols = jobs_with_w2v.columns

resumes_renamed = resumes_with_w2v.select(
    [col(c).alias(f"resume_{c}") for c in resume_cols]
)
jobs_renamed = jobs_with_w2v.select([col(c).alias(f"job_{c}") for c in job_cols])

print("[5/6] 计算匹配分数（笛卡尔积）...")
matches = resumes_renamed.crossJoin(jobs_renamed)

# 计算 TF-IDF 和 Word2Vec 余弦相似度
matches = matches.withColumn(
    "tfidf_sim",
    cosine_sim_udf(col("resume_tfidf_features"), col("job_tfidf_features")),
)
matches = matches.withColumn(
    "w2v_sim", cosine_sim_udf(col("resume_w2v_vector"), col("job_w2v_vector"))
)

# 计算所有维度分数
matches = matches.withColumn(
    "scores",
    calc_all_scores_udf(
        struct([col(f"resume_{c}") for c in resume_cols]),
        struct([col(f"job_{c}") for c in job_cols]),
        col("tfidf_sim"),
        col("w2v_sim"),
    ),
)

# 展开 scores struct 并选择输出列
result_df = matches.select(
    col("resume_resume_id").alias("resume_id"),
    col("resume_name").alias("resume_name"),
    col("job_job_id").alias("job_id"),
    col("job_job_title").alias("job_title"),
    col("job_department").alias("department"),
    col("scores.tfidf_score"),
    col("scores.word2vec_score"),
    col("scores.semantic_score"),
    col("scores.skill_score"),
    col("scores.education_score"),
    col("scores.experience_score"),
    col("scores.city_score"),
    col("scores.salary_score"),
    col("scores.certificate_score"),
    col("scores.total_score"),
    col("scores.matched_skills"),
    col("scores.missing_skills"),
    col("scores.reason"),
)

match_count = result_df.count()
print(f"  计算完成，生成 {match_count} 条匹配记录")

print("[6/6] 写入匹配结果和保存模型...")
result_df.coalesce(1).write.mode("overwrite").csv(
    f"{HDFS_BASE}/output/matches", header=True
)

# 保存模型到 HDFS（目录格式）
cv_model.write().overwrite().save(
    f"{HDFS_BASE}/models/count_vectorizer/cv_v{MODEL_VERSION}"
)
idf_model.write().overwrite().save(f"{HDFS_BASE}/models/tfidf/tfidf_v{MODEL_VERSION}")
w2v_model.write().overwrite().save(
    f"{HDFS_BASE}/models/word2vec/w2v_v{MODEL_VERSION}"
)

print(f"[{datetime.now()}] 批处理任务完成！")
spark.stop()
