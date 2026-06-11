import json
import os
import sys
from datetime import datetime

from pyspark.ml.feature import CountVectorizer, IDF, Word2Vec
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    array,
    array_remove,
    coalesce,
    col,
    from_json,
    size,
    split,
    struct,
    transform,
    trim,
    udf,
)
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)

HDFS_BASE = os.getenv("HDFS_BASE", "hdfs://localhost:9000/resume_matching")
MODEL_VERSION = datetime.now().strftime("%Y%m%d%H%M")
SEMANTIC_WEIGHTS = {"tfidf": 0.60, "word2vec": 0.40}
RULE_WEIGHTS = {
    "skill": 0.40,
    "education": 0.20,
    "experience": 0.15,
    "city": 0.10,
    "salary": 0.10,
    "certificate": 0.05,
}
TOTAL_WEIGHTS = {"semantic": 0.60, "rule": 0.40}
# 数据不足跳过时的退出码，调度器据此区分「跳过」和「成功/失败」
EXIT_CODE_SKIPPED = 3
TOTAL_STAGES = 6


def report_progress(index, stage, message=""):
    """向 stdout 输出阶段进度，调度器解析 ##PROGRESS## 行实时更新状态"""
    print(f"[{index}/{TOTAL_STAGES}] {message}")
    payload = json.dumps(
        {"index": index, "total": TOTAL_STAGES, "stage": stage, "message": message},
        ensure_ascii=False,
    )
    print(f"##PROGRESS##{payload}", flush=True)


class InsufficientTrainingData(Exception):
    pass


@udf(returnType=DoubleType())
def cosine_sim_udf(v1, v2):
    if v1 is None or v2 is None:
        return 0.0
    dot = float(v1.dot(v2))
    norm_product = float(v1.norm(2) * v2.norm(2))
    if norm_product == 0:
        return 0.0
    similarity = dot / norm_product
    return max(0.0, min(100.0, (similarity + 1) / 2 * 100))


def score_skill(resume_skills, required_skills, preferred_skills):
    resume_set = {skill for skill in resume_skills if skill}
    required_set = {skill for skill in required_skills if skill}
    preferred_set = {skill for skill in preferred_skills if skill}

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
    return 100.0 if any(certifications) else 60.0


def display_skills(skills):
    return "、".join(sorted(skills)) if skills else "无"


def build_reason(scores, matched, missing):
    reasons = [
        f"共同技能：{display_skills(matched)}",
        f"缺失技能：{display_skills(missing)}",
    ]

    if scores["semantic_score"] >= 80:
        reasons.append("文本语义高度匹配")
    elif scores["semantic_score"] >= 50:
        reasons.append("文本语义部分匹配")
    else:
        reasons.append("文本语义匹配较低")

    reasons.append(
        "学历满足要求" if scores["education_score"] == 100 else "学历未满足要求"
    )
    reasons.append(
        "经验满足要求"
        if scores["experience_score"] == 100
        else "经验未完全满足要求"
    )
    reasons.append("城市匹配" if scores["city_score"] == 100 else "城市未完全匹配")
    reasons.append(
        "薪资满足预期" if scores["salary_score"] == 100 else "薪资未完全满足预期"
    )
    reasons.append(
        "持有相关证书" if scores["certificate_score"] == 100 else "暂无相关证书"
    )
    return "；".join(reasons)


def calculate_scores(resume, job, tfidf_score, word2vec_score):
    semantic_score = (
        tfidf_score * SEMANTIC_WEIGHTS["tfidf"]
        + word2vec_score * SEMANTIC_WEIGHTS["word2vec"]
    )
    skill_score, matched, missing = score_skill(
        resume.standard_skills_array or [],
        job.required_skills_standard_array or [],
        job.preferred_skills_standard_array or [],
    )

    scores = {
        "tfidf_score": tfidf_score,
        "word2vec_score": word2vec_score,
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "education_score": score_education(
            int(resume.education_level or 0),
            int(job.education_required_level or 0),
        ),
        "experience_score": score_experience(
            int(resume.experience_years_num or 0),
            int(job.experience_required_num or 0),
        ),
        "city_score": score_city(
            str(resume.standard_location or "未知"),
            str(job.standard_location or "未知"),
        ),
        "salary_score": score_salary(
            int(resume.expected_salary or 0),
            int(job.salary_max or 0),
        ),
        "certificate_score": score_certificate(
            resume.certification_items_array or []
        ),
    }
    scores["rule_score"] = sum(
        scores[f"{name}_score"] * weight for name, weight in RULE_WEIGHTS.items()
    )
    scores["total_score"] = (
        scores["semantic_score"] * TOTAL_WEIGHTS["semantic"]
        + scores["rule_score"] * TOTAL_WEIGHTS["rule"]
    )
    scores["matched_skills"] = "|".join(sorted(matched))
    scores["missing_skills"] = "|".join(sorted(missing))
    scores["reason"] = build_reason(scores, matched, missing)
    return scores


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
        StructField("rule_score", DoubleType(), False),
        StructField("total_score", DoubleType(), False),
        StructField("matched_skills", StringType(), False),
        StructField("missing_skills", StringType(), False),
        StructField("reason", StringType(), False),
    ]
)


@udf(returnType=score_schema)
def calc_all_scores_udf(resume, job, tfidf_score, word2vec_score):
    scores = calculate_scores(resume, job, tfidf_score, word2vec_score)
    return tuple(
        round(scores[field.name], 4)
        if isinstance(scores[field.name], float)
        else scores[field.name]
        for field in score_schema.fields
    )


def empty_string_array():
    return array().cast(ArrayType(StringType()))


def pipe_array(column_name):
    values = transform(split(col(column_name), "\\|"), lambda value: trim(value))
    return coalesce(array_remove(values, ""), empty_string_array())


def prepare_input_data(resumes_df, jobs_df):
    resumes_df = (
        resumes_df.withColumn(
            "tokens",
            coalesce(
                from_json(col("tokens"), ArrayType(StringType())),
                empty_string_array(),
            ),
        )
        .withColumn("standard_skills_array", pipe_array("standard_skills"))
        .withColumn(
            "certification_items_array",
            pipe_array("certification_items"),
        )
    )
    jobs_df = (
        jobs_df.withColumn(
            "tokens",
            coalesce(
                from_json(col("tokens"), ArrayType(StringType())),
                empty_string_array(),
            ),
        )
        .withColumn(
            "required_skills_standard_array",
            pipe_array("required_skills_standard"),
        )
        .withColumn(
            "preferred_skills_standard_array",
            pipe_array("preferred_skills_standard"),
        )
    )
    return resumes_df, jobs_df


def fit_feature_models(train_df):
    if not train_df.take(1):
        raise InsufficientTrainingData("没有可用于训练的 tokens")

    cv = CountVectorizer(
        inputCol="tokens",
        outputCol="raw_features",
        vocabSize=500,
        minDF=2,
    )
    cv_model = cv.fit(train_df)
    if not cv_model.vocabulary:
        raise InsufficientTrainingData("没有词汇满足 CountVectorizer minDF=2")

    train_with_cv = cv_model.transform(train_df)
    idf_model = IDF(
        inputCol="raw_features",
        outputCol="tfidf_features",
    ).fit(train_with_cv)
    report_progress(3, "train_word2vec", "训练 Word2Vec 模型（100 维 × 30 轮迭代）...")
    w2v_model = Word2Vec(
        inputCol="tokens",
        outputCol="w2v_vector",
        vectorSize=100,
        windowSize=5,
        minCount=1,
        maxIter=30,
        seed=42,
    ).fit(train_df)
    return cv_model, idf_model, w2v_model


def entity_struct(prefix, columns):
    return struct(*[col(f"{prefix}_{name}").alias(name) for name in columns])


def create_spark_session():
    spark = (
        SparkSession.builder.appName("BatchMatching")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def run_batch_job(spark):
    print(f"[{datetime.now()}] 开始批处理任务...")
    report_progress(1, "load_data", "从 HDFS 读取和预处理数据...")
    resumes_df = spark.read.csv(
        f"{HDFS_BASE}/processed/resumes",
        header=True,
        inferSchema=True,
    )
    jobs_df = spark.read.csv(
        f"{HDFS_BASE}/processed/jobs",
        header=True,
        inferSchema=True,
    )
    resumes_df, jobs_df = prepare_input_data(resumes_df, jobs_df)

    resume_count = resumes_df.count()
    job_count = jobs_df.count()
    report_progress(1, "load_data", f"简历 {resume_count} 份 · 岗位 {job_count} 个")
    if resume_count == 0 or job_count == 0:
        raise InsufficientTrainingData("简历或岗位数据为空")

    report_progress(2, "train_tfidf", "训练 TF-IDF 模型（CountVectorizer + IDF）...")
    train_df = resumes_df.select("tokens").union(jobs_df.select("tokens"))
    train_df = train_df.filter(size(col("tokens")) > 0)
    cv_model, idf_model, w2v_model = fit_feature_models(train_df)

    report_progress(4, "vectorize", "生成 TF-IDF 与 Word2Vec 语义向量...")
    resumes_with_vectors = w2v_model.transform(
        idf_model.transform(cv_model.transform(resumes_df))
    )
    jobs_with_vectors = w2v_model.transform(
        idf_model.transform(cv_model.transform(jobs_df))
    )

    resume_cols = resumes_with_vectors.columns
    job_cols = jobs_with_vectors.columns
    resumes_renamed = resumes_with_vectors.select(
        [col(name).alias(f"resume_{name}") for name in resume_cols]
    )
    jobs_renamed = jobs_with_vectors.select(
        [col(name).alias(f"job_{name}") for name in job_cols]
    )

    report_progress(
        5,
        "match",
        f"构建匹配管道（{resume_count} × {job_count} = {resume_count * job_count} 条候选）...",
    )
    matches = resumes_renamed.crossJoin(jobs_renamed)
    matches = matches.withColumn(
        "tfidf_score",
        cosine_sim_udf(
            col("resume_tfidf_features"),
            col("job_tfidf_features"),
        ),
    ).withColumn(
        "word2vec_score",
        cosine_sim_udf(
            col("resume_w2v_vector"),
            col("job_w2v_vector"),
        ),
    )
    matches = matches.withColumn(
        "scores",
        calc_all_scores_udf(
            entity_struct("resume", resume_cols),
            entity_struct("job", job_cols),
            col("tfidf_score"),
            col("word2vec_score"),
        ),
    )

    result_df = matches.select(
        col("resume_resume_id").alias("resume_id"),
        col("resume_name").alias("resume_name"),
        col("job_job_id").alias("job_id"),
        col("job_job_title").alias("job_title"),
        col("job_department").alias("department"),
        *[col(f"scores.{field.name}") for field in score_schema.fields],
    )

    report_progress(6, "save", "执行计算并写入匹配结果、保存模型...")
    result_df.coalesce(1).write.mode("overwrite").csv(
        f"{HDFS_BASE}/output/matches",
        header=True,
    )
    cv_model.write().overwrite().save(
        f"{HDFS_BASE}/models/count_vectorizer/cv_v{MODEL_VERSION}"
    )
    idf_model.write().overwrite().save(
        f"{HDFS_BASE}/models/tfidf/tfidf_v{MODEL_VERSION}"
    )
    w2v_model.write().overwrite().save(
        f"{HDFS_BASE}/models/word2vec/w2v_v{MODEL_VERSION}"
    )
    print(f"[{datetime.now()}] 批处理任务完成！")


def main():
    spark = create_spark_session()
    try:
        run_batch_job(spark)
    except InsufficientTrainingData as error:
        print(f"训练数据不足，跳过本次任务：{error}")
        sys.exit(EXIT_CODE_SKIPPED)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
