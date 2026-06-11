# 中游 Streaming 处理

## 功能

- Spark Structured Streaming 监听 HDFS raw/ 目录
- 实时清洗：去重、缺失值处理、HTML 标签清理
- 字段标准化：学历映射、经验提取、城市统一、技能标准化
- 文本预处理：jieba 分词、停用词过滤、生成 tokens 和 clean_text
- 每 10 分钟自动退出重启（确保加载最新模型）

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
- 每个任务运行 10 分钟（600秒）后自动退出
- 自动重启新任务，从 checkpoint 恢复
- 输出日志到 `../logs/` 目录

### 方式 2：手动启动单个任务

```bash
cd streaming

# 简历清洗
spark-submit --master local[*] --driver-memory 2g streaming_resumes.py

# 岗位清洗
spark-submit --master local[*] --driver-memory 2g streaming_jobs.py
```

## 停止

```bash
pkill -f streaming_supervisor.sh
pkill -f spark-submit
```

## 数据流

```
HDFS raw/resumes/*.csv
  ↓ [数据清洗 + 字段标准化 + 文本预处理]
HDFS processed/resumes/*.csv

HDFS raw/jobs/*.csv
  ↓ [数据清洗 + 字段标准化 + 文本预处理]
HDFS processed/jobs/*.csv
```

## 清洗规则

### 简历清洗

| 字段 | 清洗操作 |
|------|---------|
| resume_id | 去重、过滤空值 |
| gender | 统一为"男/女/未知" |
| age | 提取数字、限制 16-65 范围，默认 22 |
| education | 映射为"博士/硕士/本科/大专/高中/未知" |
| education_level | 学历等级（博士=5、硕士=4、本科=3、大专=2、高中=1、未知=0） |
| skills | 清理 HTML、统一别名（py→Python）、管道符分隔 |
| standard_skills | 标准化后的技能（管道符分隔） |
| years_experience | 提取数字、支持中文数字（一年→1） |
| experience_years_num | 经验年限数值 |
| location | 清理空格 |
| standard_location | 统一城市名（南昌市→南昌、江西南昌→南昌） |
| expected_salary | 提取数字、限制 0-100 范围 |
| tokens | jieba 分词结果（JSON 数组） |
| clean_text | 过滤停用词后的文本（空格分隔） |

### 岗位清洗

| 字段 | 清洗操作 |
|------|---------|
| job_id | 去重、过滤空值 |
| education_required | 映射为"博士/硕士/本科/大专/高中/未知" |
| education_required_level | 学历要求等级 |
| skills_required | 清理 HTML、统一别名、管道符分隔 |
| required_skills_standard | 标准化必备技能 |
| skills_preferred | 清理 HTML、统一别名、管道符分隔 |
| preferred_skills_standard | 标准化加分技能 |
| experience_required | 提取数字 |
| experience_required_num | 经验要求数值 |
| location | 清理空格 |
| standard_location | 统一城市名 |
| salary_range | 解析"8-12万/年" |
| salary_min, salary_max | 薪资最小值和最大值 |
| tokens | jieba 分词结果（JSON 数组） |
| clean_text | 过滤停用词后的文本（空格分隔） |

## 字段格式

- **技能字段**：使用管道符 `|` 分隔，例如 `Python|SQL|Spark`
- **Token 字段**：JSON 数组字符串，例如 `["Python", "数据分析", "机器学习"]`
- **Clean Text 字段**：空格分隔的文本，例如 `Python 数据分析 机器学习`

## Checkpoint 管理

修改代码后需要清理 checkpoint：

```bash
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_resumes/
hdfs dfs -rm -r /resume_matching/checkpoints/streaming_jobs/
```

## 日志

- 简历任务：`../logs/streaming_resumes.log`
- 岗位任务：`../logs/streaming_jobs.log`
