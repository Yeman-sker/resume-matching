# ADR-003: 后端 API 增强

## 状态

已批准（Accepted）

## 背景

当前后端（`web_backend/main.py`，端口 8002）仅提供：

1. `GET /` — 返回欢迎消息
2. `WebSocket /ws` — 每 2 秒推送系统状态（生成器状态、Streaming 状态、批处理状态、数据计数、最后更新时间）

PRD 要求前端具备以下功能，但后端缺少对应 API：

- 获取所有岗位列表
- 获取所有简历列表
- 获取岗位匹配的简历（Top-N）
- 获取简历推荐的岗位（Top-N）
- 获取匹配详情（各维度分数、共同技能、缺失技能、推荐理由）
- 控制数据生成器的启停

### 数据存储

所有业务数据存储在 HDFS CSV 文件中：

- 简历数据：`/resume_matching/processed/resumes/part-*.csv`
- 岗位数据：`/resume_matching/processed/jobs/part-*.csv`
- 匹配结果：`/resume_matching/output/matches/part-*.csv`

## 决策

在现有 FastAPI 后端中新增 6 个 REST API 接口和 2 个控制接口。

### 3.1 新增 API 接口清单

| 方法 | 路径 | 功能 | 数据来源 |
|------|------|------|----------|
| GET | `/api/jobs` | 获取所有岗位 | HDFS processed/jobs |
| GET | `/api/resumes` | 获取所有简历 | HDFS processed/resumes |
| GET | `/api/jobs/{job_id}/matches` | 岗位匹配的简历 | HDFS output/matches |
| GET | `/api/resumes/{resume_id}/recommendations` | 简历推荐的岗位 | HDFS output/matches |
| GET | `/api/matches/{resume_id}/{job_id}` | 匹配详情 | HDFS output/matches |
| GET | `/api/stats` | 统计数据 | HDFS count aggregation |
| POST | `/api/generator/start` | 启动数据生成器 | 转发到 8000 端口 |
| POST | `/api/generator/stop` | 停止数据生成器 | 转发到 8000 端口 |

### 3.2 详细接口定义

#### `GET /api/jobs`

**查询参数**：
- `department`（可选）：按部门筛选
- `search`（可选）：按岗位名称搜索
- `page`（可选，默认 1）：分页页码
- `page_size`（可选，默认 50）：每页数量

**响应**：
```json
{
  "total": 456,
  "page": 1,
  "page_size": 50,
  "jobs": [
    {
      "job_id": "JOB_001",
      "job_title": "Python开发工程师",
      "department": "技术部",
      "location": "南昌",
      "standard_location": "南昌",
      "education_required": "本科",
      "education_required_level": 3,
      "experience_required": "1-3年",
      "experience_required_num": 2,
      "skills_required": "Python|SQL|Spark",
      "skills_preferred": "Hadoop|Hive",
      "salary_range": "8-12万/年",
      "salary_min": 8,
      "salary_max": 12,
      "job_description": "...",
      "responsibilities": "...",
      "requirements": "..."
    }
  ]
}
```

#### `GET /api/resumes`

**查询参数**：
- `search`（可选）：按姓名搜索
- `page`（可选，默认 1）
- `page_size`（可选，默认 50）

**响应**：类似 `/api/jobs`

#### `GET /api/jobs/{job_id}/matches`

**查询参数**：
- `limit`（可选，默认 50）：返回数量
- `offset`（可选，默认 0）：偏移量

**响应**：
```json
{
  "job_id": "JOB_001",
  "job_title": "Python开发工程师",
  "total_matches": 1234,
  "matches": [
    {
      "resume_id": "RES_001",
      "resume_name": "张三",
      "education": "本科",
      "years_experience": "2年",
      "skills": "Python|SQL|Spark",
      "total_score": 85.6,
      "semantic_score": 88.2,
      "rule_score": 82.0,
      "skill_score": 90.0,
      "education_score": 100.0,
      "experience_score": 85.0,
      "city_score": 100.0,
      "salary_score": 70.0,
      "certificate_score": 50.0,
      "matched_skills": "Python|SQL|Pandas",
      "missing_skills": "Spark|Hadoop",
      "reason": "..."
    }
  ]
}
```

#### `GET /api/resumes/{resume_id}/recommendations`

响应结构与 `/api/jobs/{job_id}/matches` 类似，但岗位和简历角色互换。

#### `GET /api/matches/{resume_id}/{job_id}`

**响应**：
```json
{
  "resume": { "resume_id": "RES_001", "name": "张三", "..." : "..." },
  "job": { "job_id": "JOB_001", "job_title": "Python开发工程师", "..." : "..." },
  "scores": {
    "total_score": 85.6,
    "semantic_score": 88.2,
    "tfidf_score": 90.5,
    "word2vec_score": 84.8,
    "rule_score": 82.0,
    "skill_score": 90.0,
    "education_score": 100.0,
    "experience_score": 85.0,
    "city_score": 100.0,
    "salary_score": 70.0,
    "certificate_score": 50.0
  },
  "matched_skills": ["Python", "SQL", "Pandas"],
  "missing_skills": ["Spark", "Hadoop"],
  "reason": "推荐理由..."
}
```

#### `GET /api/stats`

**响应**：
```json
{
  "total_resumes": 1234,
  "total_jobs": 456,
  "total_matches": 55704,
  "avg_total_score": 65.3,
  "max_total_score": 98.7,
  "score_distribution": {
    "semantic_score_avg": 68.2,
    "skill_score_avg": 72.1,
    "education_score_avg": 80.5,
    "experience_score_avg": 60.8,
    "city_score_avg": 55.0,
    "salary_score_avg": 65.2,
    "certificate_score_avg": 58.0
  },
  "departments": ["技术部", "数据部", "产品部", "运营部", "市场部"]
}
```

#### `POST /api/generator/start` / `POST /api/generator/stop`

代理到数据生成器（端口 8000）的对应接口。

### 3.3 HDFS 数据读取策略

#### 缓存策略

```python
from functools import lru_cache
import time

CACHE_TTL = 60  # 1 分钟缓存

class HDFSCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str, fetch_func, ttl: int = CACHE_TTL):
        now = time.monotonic()
        if key in self._cache and now - self._timestamps[key] < ttl:
            return self._cache[key]
        data = fetch_func()
        self._cache[key] = data
        self._timestamps[key] = now
        return data

hdfs_cache = HDFSCache()
```

#### CSV 读取函数

```python
import subprocess
import pandas as pd
import io

def read_hdfs_csv(path: str) -> pd.DataFrame:
    result = subprocess.run(
        ["hdfs", "dfs", "-cat", f"{path}/part-*.csv"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0 or not result.stdout.strip():
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(result.stdout), encoding="utf-8-sig")
```

### 3.4 文件结构补充

```
web_backend/
├── main.py              # 已有，需扩展
├── api/
│   ├── __init__.py
│   ├── jobs.py          # 岗位相关 API
│   ├── resumes.py       # 简历相关 API
│   ├── matches.py       # 匹配相关 API
│   ├── stats.py         # 统计数据 API
│   └── generator.py     # 生成器控制 API
├── services/
│   ├── __init__.py
│   ├── hdfs_reader.py   # HDFS CSV 读取 + 缓存
│   └── cache.py         # 缓存管理
└── start.sh             # 已有
```

## 影响

### 优点

1. **前后端分离**：前端通过标准 REST API 获取数据，不直接访问 HDFS
2. **缓存优化**：服务端缓存避免频繁 HDFS 读取，60 秒 TTL 平衡实时性和性能
3. **分页支持**：大数据集通过分页控制响应大小
4. **代理模式**：生成器控制通过后端代理，前端只需与 8002 端口交互

### 缺点

1. **HDFS 命令行延迟**：subprocess 调用 `hdfs dfs -cat` 有进程创建开销
2. **缓存一致性**：数据更新后最长 60 秒延迟
3. **无持久数据库**：直接读取 HDFS CSV，大数据量下内存压力较大

### 风险缓解

- 大数据量分页：API 支持 `page` 和 `page_size` 参数
- 缓存 TTL 可配置：通过环境变量调整
- 未来优化：可引入 SQLite 或 DuckDB 作为中间缓存层

---

**日期**: 2026-06-11
**作者**: 项目组