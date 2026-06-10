import sys
import json
import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, trim, regexp_replace, when
from pyspark.sql.types import StringType, IntegerType, ArrayType
import jieba

# 初始化 Spark
spark = SparkSession.builder \
    .appName("StreamingJobs") \
    .config("spark.sql.streaming.checkpointLocation", "hdfs://localhost:9000/resume_matching/checkpoints/streaming_jobs") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 加载资源
stopwords = set()
skill_alias = {}

try:
    import subprocess
    subprocess.run(["hdfs", "dfs", "-get", "hdfs://localhost:9000/resume_matching/resources/stopwords.json", "/tmp/stopwords.json"], check=True)
    with open("/tmp/stopwords.json") as f:
        stopwords = set(json.load(f))
except:
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

try:
    subprocess.run(["hdfs", "dfs", "-get", "hdfs://localhost:9000/resume_matching/resources/skill_alias.json", "/tmp/skill_alias.json"], check=True)
    with open("/tmp/skill_alias.json") as f:
        skill_alias = json.load(f)
except:
    skill_alias = {"py": "Python", "js": "JavaScript", "java": "Java", "cpp": "C++", "c++": "C++"}


def clean_html(text):
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', str(text))


def normalize_education(edu):
    edu = str(edu).lower().strip()
    mapping = {
        "bachelor": "本科", "master": "硕士", "doctor": "博士", "phd": "博士",
        "大学": "本科", "研究生": "硕士", "专科": "大专", "college": "大专"
    }
    for k, v in mapping.items():
        if k in edu:
            return v
    if edu in ["本科", "硕士", "博士", "大专"]:
        return edu
    return "本科"


def normalize_city(city):
    city = str(city).strip()
    mapping = {
        "beijing": "北京", "bj": "北京", "shanghai": "上海", "sh": "上海",
        "guangzhou": "广州", "gz": "广州", "shenzhen": "深圳", "sz": "深圳",
        "hangzhou": "杭州", "hz": "杭州", "chengdu": "成都", "cd": "成都"
    }
    return mapping.get(city.lower(), city)


def extract_experience_years(exp):
    exp_str = str(exp)
    match = re.search(r'(\d+)', exp_str)
    if match:
        return int(match.group(1))
    chinese_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for cn, num in chinese_num.items():
        if cn in exp_str:
            return num
    return 0


def normalize_salary(salary):
    salary_str = str(salary)
    salary_str = re.sub(r'[kK]', '000', salary_str)
    salary_str = re.sub(r'[~～]', '-', salary_str)
    matches = re.findall(r'(\d+)', salary_str)
    if len(matches) >= 2:
        return f"{matches[0]}-{matches[1]}"
    elif len(matches) == 1:
        return f"{matches[0]}-{matches[0]}"
    return "0-0"


def tokenize_and_filter(text):
    if not text:
        return []
    tokens = jieba.lcut(clean_html(str(text)))
    return [t for t in tokens if t.strip() and t not in stopwords and len(t) > 1]


def normalize_skills(skills_str):
    if not skills_str:
        return json.dumps([])
    cleaned = clean_html(str(skills_str))
    skills = [s.strip() for s in re.split(r'[,，、]', cleaned) if s.strip()]
    normalized = [skill_alias.get(s.lower(), s) for s in skills]
    return json.dumps(list(set(normalized)))


# 注册 UDF
clean_html_udf = udf(clean_html, StringType())
normalize_education_udf = udf(normalize_education, StringType())
normalize_city_udf = udf(normalize_city, StringType())
extract_experience_udf = udf(extract_experience_years, IntegerType())
normalize_salary_udf = udf(normalize_salary, StringType())
tokenize_udf = udf(tokenize_and_filter, ArrayType(StringType()))
normalize_skills_udf = udf(normalize_skills, StringType())

# 读取流数据
df = spark.readStream \
    .format("csv") \
    .option("header", "true") \
    .option("maxFilesPerTrigger", 1) \
    .load("hdfs://localhost:9000/resume_matching/raw/jobs")

# 数据清洗
cleaned_df = df \
    .filter(col("job_id").isNotNull()) \
    .dropDuplicates(["job_id"]) \
    .withColumn("title", clean_html_udf(col("title"))) \
    .withColumn("company", clean_html_udf(col("company"))) \
    .withColumn("required_skills", normalize_skills_udf(col("required_skills"))) \
    .withColumn("required_education", normalize_education_udf(col("required_education"))) \
    .withColumn("required_experience", extract_experience_udf(col("required_experience"))) \
    .withColumn("city", normalize_city_udf(col("city"))) \
    .withColumn("salary_range", normalize_salary_udf(col("salary_range"))) \
    .withColumn("required_certificates", clean_html_udf(col("required_certificates"))) \
    .withColumn("tokens", tokenize_udf(col("title")))

# 写入 HDFS
query = cleaned_df.writeStream \
    .outputMode("append") \
    .format("csv") \
    .option("header", "true") \
    .option("path", "hdfs://localhost:9000/resume_matching/processed/jobs") \
    .option("checkpointLocation", "hdfs://localhost:9000/resume_matching/checkpoints/streaming_jobs") \
    .start()

query.awaitTermination(600)  # 10 分钟后自动退出
spark.stop()
