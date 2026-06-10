import os
import json
import pickle
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, explode
from pyspark.sql.types import FloatType, StringType, ArrayType
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
import numpy as np

# 初始化 Spark
spark = SparkSession.builder \
    .appName("BatchMatching") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

HDFS_BASE = "hdfs://localhost:9000/resume_matching"
MODEL_VERSION = datetime.now().strftime("%Y%m%d%H%M")

print(f"[{datetime.now()}] 开始批处理任务...")

# 1. 读取清洗后的数据
print("[1/5] 读取数据...")
resumes_df = spark.read.csv(f"{HDFS_BASE}/processed/resumes", header=True, inferSchema=True)
jobs_df = spark.read.csv(f"{HDFS_BASE}/processed/jobs", header=True, inferSchema=True)

resume_count = resumes_df.count()
job_count = jobs_df.count()
print(f"  简历数: {resume_count}, 岗位数: {job_count}")

if resume_count == 0 or job_count == 0:
    print("数据不足，跳过本次任务")
    spark.stop()
    exit(0)

# 2. 训练 TF-IDF 模型
print("[2/5] 训练 TF-IDF 模型...")
resume_texts = resumes_df.select("resume_id", "tokens").collect()
job_texts = jobs_df.select("job_id", "tokens").collect()

resume_corpus = {r.resume_id: " ".join(eval(r.tokens) if isinstance(r.tokens, str) else r.tokens) for r in resume_texts if r.tokens}
job_corpus = {j.job_id: " ".join(eval(j.tokens) if isinstance(j.tokens, str) else j.tokens) for j in job_texts if j.tokens}

all_texts = list(resume_corpus.values()) + list(job_corpus.values())
tfidf = TfidfVectorizer(max_features=500)
tfidf.fit(all_texts)

# 保存模型到本地
os.makedirs("/tmp/models", exist_ok=True)
with open(f"/tmp/models/tfidf_v{MODEL_VERSION}.pkl", "wb") as f:
    pickle.dump(tfidf, f)

# 3. 训练 Word2Vec 模型
print("[3/5] 训练 Word2Vec 模型...")
all_tokens = []
for r in resume_texts:
    if r.tokens:
        tokens = eval(r.tokens) if isinstance(r.tokens, str) else r.tokens
        all_tokens.append(tokens)
for j in job_texts:
    if j.tokens:
        tokens = eval(j.tokens) if isinstance(j.tokens, str) else j.tokens
        all_tokens.append(tokens)

w2v = Word2Vec(sentences=all_tokens, vector_size=100, window=5, min_count=1, workers=4)
w2v.save(f"/tmp/models/word2vec_v{MODEL_VERSION}.model")

# 4. 计算匹配分数
print("[4/5] 计算匹配分数...")

def calc_tfidf_score(resume_text, job_text):
    try:
        vecs = tfidf.transform([resume_text, job_text]).toarray()
        sim = cosine_similarity([vecs[0]], [vecs[1]])[0][0]
        return float((sim + 1) / 2 * 100)
    except:
        return 0.0

def calc_w2v_score(resume_tokens, job_tokens):
    try:
        r_tokens = eval(resume_tokens) if isinstance(resume_tokens, str) else resume_tokens
        j_tokens = eval(job_tokens) if isinstance(job_tokens, str) else job_tokens

        r_vec = np.mean([w2v.wv[t] for t in r_tokens if t in w2v.wv], axis=0)
        j_vec = np.mean([w2v.wv[t] for t in j_tokens if t in w2v.wv], axis=0)

        if len(r_vec) == 0 or len(j_vec) == 0:
            return 0.0

        sim = np.dot(r_vec, j_vec) / (np.linalg.norm(r_vec) * np.linalg.norm(j_vec))
        return float((sim + 1) / 2 * 100)
    except:
        return 0.0

def calc_skill_score(resume_skills, job_skills):
    try:
        r_skills = set(json.loads(resume_skills) if isinstance(resume_skills, str) else resume_skills)
        j_skills = set(json.loads(job_skills) if isinstance(job_skills, str) else job_skills)
        if not j_skills:
            return 100.0
        match = len(r_skills & j_skills)
        return float(match / len(j_skills) * 100)
    except:
        return 0.0

def calc_education_score(resume_edu, job_edu):
    edu_rank = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
    r_rank = edu_rank.get(resume_edu, 2)
    j_rank = edu_rank.get(job_edu, 2)
    return 100.0 if r_rank >= j_rank else max(0, 100 - (j_rank - r_rank) * 20)

def calc_experience_score(resume_exp, job_exp):
    try:
        r_exp = int(resume_exp) if resume_exp else 0
        j_exp = int(job_exp) if job_exp else 0
        if r_exp >= j_exp:
            return 100.0
        return max(0, 100 - (j_exp - r_exp) * 15)
    except:
        return 0.0

def calc_city_score(resume_city, job_city):
    return 100.0 if resume_city == job_city else 0.0

def calc_salary_score(resume_salary, job_salary):
    try:
        r_min, r_max = map(int, resume_salary.split("-"))
        j_min, j_max = map(int, job_salary.split("-"))
        r_avg = (r_min + r_max) / 2
        j_avg = (j_min + j_max) / 2
        diff = abs(r_avg - j_avg) / max(j_avg, 1)
        return max(0, 100 - diff * 50)
    except:
        return 50.0

def calc_cert_score(resume_certs, job_certs):
    try:
        r_certs = set(c.strip() for c in resume_certs.split(",") if c.strip())
        j_certs = set(c.strip() for c in job_certs.split(",") if c.strip())
        if not j_certs:
            return 100.0
        match = len(r_certs & j_certs)
        return float(match / len(j_certs) * 100)
    except:
        return 0.0

# 笛卡尔积计算
results = []
for resume in resumes_df.collect():
    r_id = resume.resume_id
    r_text = resume_corpus.get(r_id, "")
    r_tokens = resume.tokens

    for job in jobs_df.collect():
        j_id = job.job_id
        j_text = job_corpus.get(j_id, "")
        j_tokens = job.tokens

        # 语义分
        tfidf_score = calc_tfidf_score(r_text, j_text)
        w2v_score = calc_w2v_score(r_tokens, j_tokens)
        semantic_score = tfidf_score * 0.6 + w2v_score * 0.4

        # 规则分
        skill_score = calc_skill_score(resume.skills, job.required_skills)
        edu_score = calc_education_score(resume.education, job.required_education)
        exp_score = calc_experience_score(resume.experience_years, job.required_experience)
        city_score = calc_city_score(resume.city, job.city)
        salary_score = calc_salary_score(resume.expected_salary, job.salary_range)
        cert_score = calc_cert_score(resume.certificates, job.required_certificates)

        rule_score = (skill_score * 0.4 + edu_score * 0.2 + exp_score * 0.15 +
                      city_score * 0.1 + salary_score * 0.1 + cert_score * 0.05)

        # 总分
        total_score = semantic_score * 0.6 + rule_score * 0.4

        results.append({
            "resume_id": r_id,
            "job_id": j_id,
            "total_score": round(total_score, 2),
            "semantic_score": round(semantic_score, 2),
            "rule_score": round(rule_score, 2),
            "skill_score": round(skill_score, 2),
            "education_score": round(edu_score, 2),
            "experience_score": round(exp_score, 2),
            "city_score": round(city_score, 2),
            "salary_score": round(salary_score, 2),
            "certificate_score": round(cert_score, 2)
        })

print(f"  计算完成，生成 {len(results)} 条匹配记录")

# 5. 写入结果
print("[5/5] 写入匹配结果...")
result_df = spark.createDataFrame(results)
result_df.coalesce(1).write.mode("overwrite").csv(f"{HDFS_BASE}/output/matches", header=True)

# 上传模型到 HDFS
import subprocess
subprocess.run(["hdfs", "dfs", "-put", "-f", f"/tmp/models/tfidf_v{MODEL_VERSION}.pkl", f"{HDFS_BASE}/models/tfidf/"], check=False)
subprocess.run(["hdfs", "dfs", "-put", "-f", f"/tmp/models/word2vec_v{MODEL_VERSION}.model", f"{HDFS_BASE}/models/word2vec/"], check=False)

print(f"[{datetime.now()}] 批处理任务完成！")
spark.stop()
