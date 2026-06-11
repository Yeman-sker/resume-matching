# 中游 Streaming 处理

## 功能

- Spark Structured Streaming 监听 HDFS raw/ 目录
- 实时清洗：去重、缺失值处理、HTML标签清理
- 字段标准化：学历映射、经验提取、城市统一
- 文本预处理：jieba 分词、停用词过滤、技能标准化
- 每 10 分钟自动退出重启（加载最新模型）

## 安装

```bash
bash scripts/setup_python_env.sh
```

## 上传资源到 HDFS

```bash
hdfs dfs -put streaming/stopwords.json hdfs://localhost:9000/resume_matching/resources/
hdfs dfs -put streaming/skill_alias.json hdfs://localhost:9000/resume_matching/resources/
```

## 运行

### 方式 1：监督脚本（推荐）

```bash
bash streaming/streaming_supervisor.sh
```

监督脚本会自动：
- 启动两个 Streaming 任务（简历 + 岗位）
- 每个任务运行 10 分钟后自动退出
- 自动重启新任务
- 输出日志到 `../logs/` 目录

### 方式 2：手动启动单个任务

```bash
export PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"
export PYSPARK_PYTHON="$PWD/.venv/bin/python"

# 简历清洗
spark-submit --master local[*] streaming/streaming_resumes.py

# 岗位清洗
spark-submit --master local[*] streaming/streaming_jobs.py
```

## 停止

```bash
pkill -f streaming_supervisor.sh
pkill -f spark-submit
```

## 数据流

```
HDFS raw/resumes/*.csv
  ↓ [数据清洗 + 字段标准化]
HDFS processed/resumes/*.csv

HDFS raw/jobs/*.csv
  ↓ [数据清洗 + 字段标准化]
HDFS processed/jobs/*.csv
```

## 清洗规则

### 简历清洗

| 字段 | 清洗操作 |
|------|---------|
| resume_id | 去重、过滤空值 |
| gender | 统一为"男/女/未知" |
| age | 提取数字、限制 18-65 范围 |
| education | 映射为"本科/硕士/博士/大专" |
| skills | 清理 HTML、统一别名、JSON 数组格式 |
| experience_years | 提取数字（中文数字转换） |
| city | 统一城市名（北京/上海/广州/深圳等） |
| expected_salary | 统一格式为"最低-最高" |
| major | jieba 分词、停用词过滤 |

### 岗位清洗

| 字段 | 清洗操作 |
|------|---------|
| job_id | 去重、过滤空值 |
| required_education | 映射为"本科/硕士/博士/大专" |
| required_skills | 清理 HTML、统一别名、JSON 数组格式 |
| required_experience | 提取数字 |
| city | 统一城市名 |
| salary_range | 统一格式为"最低-最高" |
| title | jieba 分词、停用词过滤 |

## Checkpoint 管理

修改代码后需要清理 checkpoint：

```bash
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_resumes/
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_jobs/
```

## 日志

- 简历任务：`../logs/streaming_resumes.log`
- 岗位任务：`../logs/streaming_jobs.log`
