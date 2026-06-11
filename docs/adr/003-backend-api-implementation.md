# ADR-003 补充：后端 API 实现规范

## 状态

已批准（Accepted）

## 接口实现细节

基于 ADR-003 的设计，本文档补充具体实现规范。

### 1. 缓存策略

**三层缓存结构**：

```python
# 第一层：DataFrame 缓存（TTL=60秒）
resumes_df: pd.DataFrame  # /resume_matching/processed/resumes
jobs_df: pd.DataFrame     # /resume_matching/processed/jobs
matches_df: pd.DataFrame  # /resume_matching/output/matches

# 第二层：计数缓存（TTL=30秒，已存在）
count_cache: (total_resumes, total_jobs, total_matches)

# 第三层：业务查询结果缓存（可选，暂不实现）
```

**缓存实现**：
- 使用 `time.monotonic()` 判断过期
- 使用 `asyncio.Lock` 防止并发重复加载
- 返回空 DataFrame 而不抛异常

### 2. 字段定义

**简历字段** (`processed/resumes`)：
- 原始字段：resume_id, name, gender, age, education, school, major, years_experience, skills, certifications, work_history, expected_salary, location, contact
- 清洗字段：education_level, experience_years_num, standard_location, standard_skills, skill_items_raw, certification_items, tokens, clean_text

**岗位字段** (`processed/jobs`)：
- 原始字段：job_id, job_title, department, location, education_required, experience_required, skills_required, skills_preferred, salary_range, job_description, responsibilities, requirements
- 清洗字段：education_required_level, experience_required_num, standard_location, required_skills_standard, preferred_skills_standard, required_skill_items_raw, preferred_skill_items_raw, salary_min, salary_max, tokens, clean_text

**匹配结果字段** (`output/matches`)：
- resume_id, resume_name, job_id, job_title, department
- tfidf_score, word2vec_score, semantic_score, skill_score, education_score, experience_score, city_score, salary_score, certificate_score, total_score
- matched_skills, missing_skills, reason

### 3. 分页与筛选规则

**分页参数**：
```python
page = max(1, page)                      # 最小为 1
page_size = max(1, min(page_size, 200))  # 限制在 1-200
start = (page - 1) * page_size
end = start + page_size
```

**搜索逻辑**：
```python
# 岗位名称搜索（模糊匹配，不区分大小写）
if search:
    df = df[df['job_title'].str.contains(search, case=False, na=False)]

# 简历姓名搜索
if search:
    df = df[df['name'].str.contains(search, case=False, na=False)]

# 部门筛选（精确匹配）
if department:
    df = df[df['department'] == department]
```

### 4. 排序与 Top-N 规则

**匹配结果排序**：
```python
# 按 total_score 降序排序
matches_df = matches_df.sort_values('total_score', ascending=False)

# limit 和 offset
limit = max(1, min(limit, 200))
offset = max(0, offset)
results = matches_df.iloc[offset:offset+limit]
```

**rule_score 计算**：
```python
# rule_score = 除语义分外的其他维度加权平均
rule_score = (
    skill_score * 0.30 +
    education_score * 0.15 +
    experience_score * 0.10 +
    city_score * 0.05 +
    salary_score * 0.05 +
    certificate_score * 0.05
) / 0.70
```

### 5. 错误处理策略

**HDFS 读取失败**：
```python
# 返回空结果，不抛异常
if df.empty:
    return {"total": 0, "page": page, "page_size": page_size, "jobs": []}
```

**资源不存在**：
```python
# 返回 404
if job_id not in jobs_df['job_id'].values:
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
```

**数据生成器不可用**：
```python
# 返回 503
try:
    response = await client.post("http://localhost:8000/control", json={"action": "start"}, timeout=5.0)
except (httpx.RequestError, httpx.TimeoutException):
    raise HTTPException(status_code=503, detail="Data generator service unavailable")
```

### 6. JOIN 策略

**匹配详情查询**：
```python
# 三表 JOIN（在内存中使用 Pandas merge）
result = matches_df.merge(resumes_df, on='resume_id', how='left') \
                   .merge(jobs_df, on='job_id', how='left')
```

**字段冲突处理**：
```python
# 使用 suffixes 避免列名冲突
result = matches_df.merge(resumes_df, on='resume_id', how='left', suffixes=('', '_resume')) \
                   .merge(jobs_df, on='job_id', how='left', suffixes=('', '_job'))
```

### 7. 响应格式规范

**分页响应**：
```json
{
  "total": 1234,
  "page": 1,
  "page_size": 50,
  "jobs": [...]
}
```

**匹配列表响应**：
```json
{
  "job_id": "JOB_001",
  "job_title": "Python开发工程师",
  "total_matches": 1234,
  "matches": [...]
}
```

**匹配详情响应**：
```json
{
  "resume": {...},
  "job": {...},
  "scores": {...},
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["Spark"],
  "reason": "..."
}
```

---

**日期**: 2026-06-11  
**作者**: 项目组
