import json
import re
import subprocess

import jieba
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, trim, udf, when
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

spark = (
    SparkSession.builder.appName("StreamingJobs")
    .config(
        "spark.sql.streaming.checkpointLocation",
        "hdfs://localhost:9000/resume_matching/checkpoints/streaming_jobs",
    )
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

RAW_SCHEMA = StructType(
    [
        StructField("job_id", StringType(), True),
        StructField("job_title", StringType(), True),
        StructField("department", StringType(), True),
        StructField("location", StringType(), True),
        StructField("education_required", StringType(), True),
        StructField("experience_required", StringType(), True),
        StructField("skills_required", StringType(), True),
        StructField("skills_preferred", StringType(), True),
        StructField("salary_range", StringType(), True),
        StructField("job_description", StringType(), True),
        StructField("responsibilities", StringType(), True),
        StructField("requirements", StringType(), True),
    ]
)

DEFAULT_STOPWORDS = {
    "的", "了", "在", "是", "和", "与", "及", "以及", "负责", "要求",
    "熟悉", "掌握", "了解", "能够", "进行", "相关", "工作", "岗位",
    "项目", "经验", "具备", "同学", "联系", "更多",
}
DEFAULT_SKILL_ALIAS = {
    "py": "Python",
    "python": "Python",
    "python编程": "Python",
    "sql": "SQL",
    "sql数据库": "SQL",
    "mysql": "MySQL",
    "mysql数据库": "MySQL",
    "pyspark": "Spark",
    "apache spark": "Spark",
    "spark": "Spark",
    "spring boot": "Spring",
    "机器学习": "Machine Learning",
    "数据分析": "Data Analysis",
    "数据统计": "Data Analysis",
    "数据可视化": "Data Visualization",
    "可视化": "Data Visualization",
    "etl开发": "ETL",
    "etl": "ETL",
}


def load_hdfs_json(hdfs_path, local_path, default):
    try:
        subprocess.run(
            ["hdfs", "dfs", "-get", "-f", hdfs_path, local_path],
            check=True,
            capture_output=True,
        )
        with open(local_path, encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


stopwords = set(
    load_hdfs_json(
        "hdfs://localhost:9000/resume_matching/resources/stopwords.json",
        "/tmp/resume_matching_stopwords.json",
        list(DEFAULT_STOPWORDS),
    )
)
loaded_alias = load_hdfs_json(
    "hdfs://localhost:9000/resume_matching/resources/skill_alias.json",
    "/tmp/resume_matching_skill_alias.json",
    DEFAULT_SKILL_ALIAS,
)
skill_alias = {str(key).lower(): value for key, value in loaded_alias.items()}
skill_alias.update(DEFAULT_SKILL_ALIAS)

EDUCATION_LEVEL = {"未知": 0, "高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}
CITY_MAP = {
    "江西南昌": "南昌",
    "南昌市": "南昌",
    "北京市": "北京",
    "上海市": "上海",
    "深圳市": "深圳",
    "杭州市": "杭州",
    "九江市": "九江",
    "beijing": "北京",
    "shanghai": "上海",
    "shenzhen": "深圳",
    "hangzhou": "杭州",
}


def clean_text(value):
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def normalize_education(value):
    text = clean_text(value)
    if "博士" in text:
        return "博士"
    if "硕士" in text or "研究生" in text:
        return "硕士"
    if "本科" in text or "bachelor" in text.lower():
        return "本科"
    if "大专" in text or "专科" in text:
        return "大专"
    if "高中" in text:
        return "高中"
    return "未知"


def education_level(value):
    return EDUCATION_LEVEL.get(normalize_education(value), 0)


def parse_experience(value):
    text = clean_text(value)
    chinese = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for key, number in chinese.items():
        if key in text:
            return number
    numbers = re.findall(r"-?\d+", text)
    years = int(numbers[0]) if numbers else 0
    return years if 0 <= years <= 40 else 0


def normalize_city(value):
    text = clean_text(value)
    if not text:
        return "未知"
    compact = text.replace(" ", "")
    return CITY_MAP.get(compact, CITY_MAP.get(compact.lower(), compact.removesuffix("市")))


def salary_values(value):
    numbers = [int(float(item)) for item in re.findall(r"\d+(?:\.\d+)?", clean_text(value))]
    if not numbers:
        return 0, 0
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return numbers[0], numbers[1]


def salary_min(value):
    return salary_values(value)[0]


def salary_max(value):
    return salary_values(value)[1]


def split_items(value):
    text = clean_text(value)
    items = [item.strip() for item in re.split(r"[,，、|]", text) if item.strip()]
    return "|".join(dict.fromkeys(items))


def normalize_skills(value):
    items_text = split_items(value)
    items = items_text.split("|") if items_text else []
    normalized = [skill_alias.get(item.lower(), item) for item in items]
    return "|".join(dict.fromkeys(normalized))


def preprocess_tokens(value):
    text = clean_text(value)
    for alias in sorted(skill_alias, key=len, reverse=True):
        text = re.sub(re.escape(alias), skill_alias[alias], text, flags=re.IGNORECASE)
    tokens = [
        token.strip()
        for token in jieba.lcut(text)
        if token.strip() and token.strip() not in stopwords
    ]
    return json.dumps(tokens, ensure_ascii=False)


def tokens_to_clean_text(value):
    try:
        return " ".join(json.loads(value or "[]"))
    except Exception:
        return ""


clean_text_udf = udf(clean_text, StringType())
normalize_education_udf = udf(normalize_education, StringType())
education_level_udf = udf(education_level, IntegerType())
parse_experience_udf = udf(parse_experience, IntegerType())
normalize_city_udf = udf(normalize_city, StringType())
salary_min_udf = udf(salary_min, IntegerType())
salary_max_udf = udf(salary_max, IntegerType())
split_items_udf = udf(split_items, StringType())
normalize_skills_udf = udf(normalize_skills, StringType())
preprocess_tokens_udf = udf(preprocess_tokens, StringType())
tokens_to_clean_text_udf = udf(tokens_to_clean_text, StringType())

df = (
    spark.readStream.format("csv")
    .schema(RAW_SCHEMA)
    .option("header", "true")
    .option("maxFilesPerTrigger", 1)
    .load("hdfs://localhost:9000/resume_matching/raw/jobs")
)

cleaned_df = (
    df.filter(col("job_id").isNotNull() & (trim(col("job_id")) != ""))
    .dropDuplicates(["job_id"])
    .withColumn("job_title", clean_text_udf(col("job_title")))
    .withColumn("department", clean_text_udf(col("department")))
    .withColumn("location", when(trim(col("location")) == "", "未知").otherwise(col("location")))
    .withColumn("education_required", normalize_education_udf(col("education_required")))
    .withColumn("skills_required", clean_text_udf(col("skills_required")))
    .withColumn("skills_preferred", clean_text_udf(col("skills_preferred")))
    .withColumn("job_description", clean_text_udf(col("job_description")))
    .withColumn("responsibilities", clean_text_udf(col("responsibilities")))
    .withColumn("requirements", clean_text_udf(col("requirements")))
    .withColumn("education_required_level", education_level_udf(col("education_required")))
    .withColumn("experience_required_num", parse_experience_udf(col("experience_required")))
    .withColumn("standard_location", normalize_city_udf(col("location")))
    .withColumn("required_skill_items_raw", split_items_udf(col("skills_required")))
    .withColumn("preferred_skill_items_raw", split_items_udf(col("skills_preferred")))
    .withColumn("salary_min", salary_min_udf(col("salary_range")))
    .withColumn("salary_max", salary_max_udf(col("salary_range")))
    .withColumn("required_skills_standard", normalize_skills_udf(col("skills_required")))
    .withColumn("preferred_skills_standard", normalize_skills_udf(col("skills_preferred")))
    .withColumn(
        "raw_text",
        concat_ws(
            " ",
            col("skills_required"),
            col("skills_preferred"),
            col("required_skills_standard"),
            col("preferred_skills_standard"),
            col("job_title"),
            col("job_description"),
            col("responsibilities"),
            col("requirements"),
        ),
    )
    .withColumn("tokens", preprocess_tokens_udf(col("raw_text")))
    .withColumn("clean_text", tokens_to_clean_text_udf(col("tokens")))
)

query = (
    cleaned_df.writeStream.outputMode("append")
    .format("csv")
    .option("header", "true")
    .option("path", "hdfs://localhost:9000/resume_matching/processed/jobs")
    .option(
        "checkpointLocation",
        "hdfs://localhost:9000/resume_matching/checkpoints/streaming_jobs",
    )
    .start()
)

query.awaitTermination(600)
spark.stop()
