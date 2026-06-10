import sys
import json
import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, trim, regexp_replace, when, lit
from pyspark.sql.types import StringType, IntegerType, ArrayType
import jieba

# 初始化 Spark
spark = SparkSession.builder \
    .appName("StreamingResumes") \
    .config("spark.sql.streaming.checkpointLocation", "hdfs://localhost:9000/resume_matching/checkpoints/streaming_resumes") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 加载停用词和技能别名（从 HDFS）
stopwords = set()
skill_alias = {}

try:
    stopwords_path = "hdfs://localhost:9000/resume_matching/resources/stopwords.json"
    with open("/tmp/stopwords.json", "w") as f:
        import subprocess
        subprocess.run(["hdfs", "dfs", "-get", stopwords_path, "/tmp/stopwords.json"], check=True)
    with open("/tmp/stopwords.json") as f:
        stopwords = set(json.load(f))
except:
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

try:
    alias_path = "hdfs://localhost:9000/resume_matching/resources/skill_alias.json"
    subprocess.run(["hdfs", "dfs", "-get", alias_path, "/tmp/skill_alias.json"], check=True)
    with open("/tmp/skill_alias.json") as f:
        skill_alias = json.load(f)
except:
    skill_alias = {"py": "Python", "js": "JavaScript", "java": "Java", "cpp": "C++", "c++": "C++"}


def clean_html(text):
    """清理 HTML 标签"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', str(text))


def normalize_education(edu):
    """标准化学历"""
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
    """标准化城市"""
    city = str(city).strip()
    mapping = {
        "beijing": "北京", "bj": "北京", "shanghai": "上海", "sh": "上海",
        "guangzhou": "广州", "gz": "广州", "shenzhen": "深圳", "sz": "深圳",
        "hangzhou": "杭州", "hz": "杭州", "chengdu": "成都", "cd": "成都"
    }
    city_lower = city.lower()
    return mapping.get(city_lower, city)


def extract_experience_years(exp):
    """提取工作年限数字"""
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
    """标准化薪资范围"""
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
    """分词 + 停用词过滤"""
    if not text:
        return []
    tokens = jieba.lcut(clean_html(str(text)))
    return [t for t in tokens if t.strip() and t not in stopwords and len(t) > 1]


def normalize_skills(skills_str):
    """标准化技能列表"""
    if not skills_str:
        return json.dumps([])

    cleaned = clean_html(str(skills_str))
    skills = [s.strip() for s in re.split(r'[,，、]', cleaned) if s.strip()]

    normalized = []
    for skill in skills:
        skill_lower = skill.lower()
        normalized.append(skill_alias.get(skill_lower, skill))

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
    .load("hdfs://localhost:9000/resume_matching/raw/resumes")

# 数据清洗
cleaned_df = df \
    .filter(col("resume_id").isNotNull()) \
    .dropDuplicates(["resume_id"]) \
    .withColumn("name", trim(col("name"))) \
    .withColumn("gender", when(col("gender").isin(["男", "女"]), col("gender")).otherwise("未知")) \
    .withColumn("age", regexp_replace(col("age"), r'\D+', '').cast(IntegerType())) \
    .withColumn("age", when(col("age").between(18, 65), col("age")).otherwise(25)) \
    .withColumn("education", normalize_education_udf(col("education"))) \
    .withColumn("major", clean_html_udf(col("major"))) \
    .withColumn("skills", normalize_skills_udf(col("skills"))) \
    .withColumn("experience_years", extract_experience_udf(col("experience_years"))) \
    .withColumn("city", normalize_city_udf(col("city"))) \
    .withColumn("expected_salary", normalize_salary_udf(col("expected_salary"))) \
    .withColumn("certificates", clean_html_udf(col("certificates"))) \
    .withColumn("tokens", tokenize_udf(col("major")))

# 写入 HDFS
query = cleaned_df.writeStream \
    .outputMode("append") \
    .format("csv") \
    .option("header", "true") \
    .option("path", "hdfs://localhost:9000/resume_matching/processed/resumes") \
    .option("checkpointLocation", "hdfs://localhost:9000/resume_matching/checkpoints/streaming_resumes") \
    .start()

query.awaitTermination(600)  # 10 分钟后自动退出
spark.stop()
