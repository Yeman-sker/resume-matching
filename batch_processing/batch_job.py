import json
import os
import pickle
import subprocess
from datetime import datetime

import numpy as np
from gensim.models import Word2Vec
from pyspark.sql import SparkSession
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def parse_tokens(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def pipe_to_set(value):
    if not value:
        return set()
    return {item.strip() for item in str(value).split("|") if item.strip()}


def similarity_to_score(similarity):
    return float(max(0.0, min(100.0, (float(similarity) + 1) / 2 * 100)))


def calc_tfidf_score(resume_text, job_text, vectorizer):
    try:
        vectors = vectorizer.transform([resume_text, job_text])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        return similarity_to_score(similarity)
    except Exception:
        return 0.0


def average_vector(tokens, model):
    vectors = [model.wv[token] for token in tokens if token in model.wv]
    if not vectors:
        return None
    return np.mean(vectors, axis=0)


def calc_w2v_score(resume_tokens, job_tokens, model):
    resume_vector = average_vector(resume_tokens, model)
    job_vector = average_vector(job_tokens, model)
    if resume_vector is None or job_vector is None:
        return 0.0
    denominator = np.linalg.norm(resume_vector) * np.linalg.norm(job_vector)
    if denominator == 0:
        return 0.0
    similarity = np.dot(resume_vector, job_vector) / denominator
    return similarity_to_score(similarity)


def score_skill(resume_skills, required_skills, preferred_skills):
    if not required_skills:
        return 60.0, set(), set()
    matched = resume_skills & required_skills
    missing = required_skills - resume_skills
    required_score = len(matched) / len(required_skills) * 85
    preferred_bonus = min(len(resume_skills & preferred_skills) * 5, 15)
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
    return 100.0 if certifications else 60.0


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

    reasons.append("学历满足要求" if scores["education_score"] == 100 else "学历与岗位要求存在差距")
    if scores["experience_score"] == 100:
        reasons.append("经验年限满足岗位要求")
    elif scores["experience_score"] >= 70:
        reasons.append("经验略低于要求，但差距不大")
    else:
        reasons.append("经验年限与岗位要求差距较大")
    reasons.append("城市匹配" if scores["city_score"] == 100 else "城市不完全匹配")
    return "；".join(reasons)


print(f"[{datetime.now()}] 开始批处理任务...")
print("[1/5] 读取数据...")
resumes_df = spark.read.csv(f"{HDFS_BASE}/processed/resumes", header=True, inferSchema=True)
jobs_df = spark.read.csv(f"{HDFS_BASE}/processed/jobs", header=True, inferSchema=True)
resumes = resumes_df.collect()
jobs = jobs_df.collect()
print(f"  简历数: {len(resumes)}, 岗位数: {len(jobs)}")

if not resumes or not jobs:
    print("数据不足，跳过本次任务")
    spark.stop()
    raise SystemExit(0)

resume_corpus = {row.resume_id: str(row.clean_text or "") for row in resumes}
job_corpus = {row.job_id: str(row.clean_text or "") for row in jobs}
resume_tokens = {row.resume_id: parse_tokens(row.tokens) for row in resumes}
job_tokens = {row.job_id: parse_tokens(row.tokens) for row in jobs}
all_texts = list(resume_corpus.values()) + list(job_corpus.values())
all_tokens = list(resume_tokens.values()) + list(job_tokens.values())

print("[2/5] 训练 TF-IDF 模型...")
tfidf = TfidfVectorizer(max_features=500, token_pattern=r"(?u)\b\w+\b")
tfidf.fit(all_texts)

os.makedirs("/tmp/models", exist_ok=True)
tfidf_path = f"/tmp/models/tfidf_v{MODEL_VERSION}.pkl"
with open(tfidf_path, "wb") as file:
    pickle.dump(tfidf, file)

print("[3/5] 训练 Word2Vec 模型...")
w2v = Word2Vec(
    sentences=all_tokens,
    vector_size=100,
    window=5,
    min_count=1,
    workers=4,
    seed=42,
    epochs=30,
)
w2v_path = f"/tmp/models/word2vec_v{MODEL_VERSION}.model"
w2v.save(w2v_path)

print("[4/5] 计算匹配分数...")
results = []
for resume in resumes:
    for job in jobs:
        tfidf_score = calc_tfidf_score(
            resume_corpus.get(resume.resume_id, ""),
            job_corpus.get(job.job_id, ""),
            tfidf,
        )
        word2vec_score = calc_w2v_score(
            resume_tokens.get(resume.resume_id, []),
            job_tokens.get(job.job_id, []),
            w2v,
        )
        semantic_score = tfidf_score * 0.60 + word2vec_score * 0.40

        skill_score, matched, missing = score_skill(
            pipe_to_set(resume.standard_skills),
            pipe_to_set(job.required_skills_standard),
            pipe_to_set(job.preferred_skills_standard),
        )
        scores = {
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
                pipe_to_set(resume.certification_items)
            ),
        }
        total_score = sum(scores[name + "_score"] * weight for name, weight in SCORE_WEIGHTS.items())

        results.append(
            {
                "resume_id": resume.resume_id,
                "resume_name": resume.name,
                "job_id": job.job_id,
                "job_title": job.job_title,
                "department": job.department,
                "tfidf_score": round(tfidf_score, 4),
                "word2vec_score": round(word2vec_score, 4),
                **{key: round(value, 4) for key, value in scores.items()},
                "total_score": round(total_score, 4),
                "matched_skills": "|".join(sorted(matched)),
                "missing_skills": "|".join(sorted(missing)),
                "reason": build_reason(scores, matched, missing),
            }
        )

print(f"  计算完成，生成 {len(results)} 条匹配记录")
print("[5/5] 写入匹配结果...")
result_df = spark.createDataFrame(results)
result_df.coalesce(1).write.mode("overwrite").csv(
    f"{HDFS_BASE}/output/matches",
    header=True,
)

subprocess.run(
    ["hdfs", "dfs", "-put", "-f", tfidf_path, f"{HDFS_BASE}/models/tfidf/"],
    check=False,
)
subprocess.run(
    ["hdfs", "dfs", "-put", "-f", w2v_path, f"{HDFS_BASE}/models/word2vec/"],
    check=False,
)

print(f"[{datetime.now()}] 批处理任务完成！")
spark.stop()
