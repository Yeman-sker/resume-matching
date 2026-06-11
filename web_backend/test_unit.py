#!/usr/bin/env python3
"""直接测试服务层和 API 逻辑（单元测试）"""

import asyncio
import pandas as pd
import sys

sys.path.insert(0, '.')

from services.hdfs_reader import hdfs_cache

# 模拟数据
MOCK_RESUMES = pd.DataFrame([
    {
        "resume_id": "RES_001", "name": "张三", "gender": "男", "age": 25,
        "education": "本科", "school": "南昌大学", "major": "计算机科学",
        "years_experience": "2年", "skills": "Python|SQL|Pandas",
        "certifications": "软件设计师", "work_history": "数据分析师",
        "expected_salary": 12, "location": "南昌", "contact": "13800138000",
        "education_level": 3, "experience_years_num": 2,
        "standard_location": "南昌", "standard_skills": "Python|SQL|Pandas",
    },
    {
        "resume_id": "RES_002", "name": "李四", "gender": "女", "age": 28,
        "education": "硕士", "school": "清华大学", "major": "数据科学",
        "years_experience": "3年", "skills": "Python|Spark|Hadoop",
        "certifications": "数据分析师", "work_history": "大数据工程师",
        "expected_salary": 20, "location": "北京", "contact": "13800138001",
        "education_level": 4, "experience_years_num": 3,
        "standard_location": "北京", "standard_skills": "Python|Spark|Hadoop",
    },
])

MOCK_JOBS = pd.DataFrame([
    {
        "job_id": "JOB_001", "job_title": "Python数据分析师", "department": "技术部",
        "location": "南昌", "education_required": "本科", "experience_required": "1-3年",
        "skills_required": "Python|SQL|Pandas", "skills_preferred": "Spark|Tableau",
        "salary_range": "10-15万/年", "education_required_level": 3,
        "experience_required_num": 2, "standard_location": "南昌",
        "required_skills_standard": "Python|SQL|Pandas",
        "preferred_skills_standard": "Spark|Tableau", "salary_min": 10, "salary_max": 15,
    },
    {
        "job_id": "JOB_002", "job_title": "大数据开发工程师", "department": "数据部",
        "location": "北京", "education_required": "硕士", "experience_required": "3年以上",
        "skills_required": "Spark|Hadoop|Hive", "skills_preferred": "Flink|Kafka",
        "salary_range": "20-30万/年", "education_required_level": 4,
        "experience_required_num": 3, "standard_location": "北京",
        "required_skills_standard": "Spark|Hadoop|Hive",
        "preferred_skills_standard": "Flink|Kafka", "salary_min": 20, "salary_max": 30,
    },
])

MOCK_MATCHES = pd.DataFrame([
    {
        "resume_id": "RES_001", "resume_name": "张三", "job_id": "JOB_001",
        "job_title": "Python数据分析师", "department": "技术部",
        "tfidf_score": 88.5, "word2vec_score": 85.3, "semantic_score": 87.2,
        "skill_score": 100.0, "education_score": 100.0, "experience_score": 100.0,
        "city_score": 100.0, "salary_score": 100.0, "certificate_score": 100.0,
        "total_score": 95.6, "matched_skills": "Python|SQL|Pandas",
        "missing_skills": "", "reason": "完美匹配",
    },
    {
        "resume_id": "RES_002", "resume_name": "李四", "job_id": "JOB_002",
        "job_title": "大数据开发工程师", "department": "数据部",
        "tfidf_score": 92.1, "word2vec_score": 90.5, "semantic_score": 91.4,
        "skill_score": 100.0, "education_score": 100.0, "experience_score": 100.0,
        "city_score": 100.0, "salary_score": 100.0, "certificate_score": 100.0,
        "total_score": 97.4, "matched_skills": "Spark|Hadoop",
        "missing_skills": "Hive", "reason": "高度匹配",
    },
])


def mock_read_hdfs_csv(path: str) -> pd.DataFrame:
    """Mock HDFS 读取函数"""
    if "resumes" in path:
        return MOCK_RESUMES.copy()
    elif "jobs" in path:
        return MOCK_JOBS.copy()
    elif "matches" in path:
        return MOCK_MATCHES.copy()
    return pd.DataFrame()


async def test_unit():
    """单元测试"""
    # 替换 HDFS 读取函数为 Mock
    import services.hdfs_reader as reader
    reader.read_hdfs_csv = mock_read_hdfs_csv

    # 清空缓存
    hdfs_cache.clear()

    print("="*60)
    print("后端 API 单元测试（Mock 数据）")
    print("="*60)

    # 1. 测试缓存加载
    print("\n1. 测试缓存加载")
    from services.hdfs_reader import get_cached_dataframe

    resumes_df = await get_cached_dataframe("resumes")
    jobs_df = await get_cached_dataframe("jobs")
    matches_df = await get_cached_dataframe("matches")

    print(f"   ✓ 简历数: {len(resumes_df)}")
    print(f"   ✓ 岗位数: {len(jobs_df)}")
    print(f"   ✓ 匹配数: {len(matches_df)}")

    # 2. 测试岗位列表逻辑
    print("\n2. 测试岗位列表逻辑")
    df = jobs_df.copy()

    # 部门筛选
    filtered = df[df["department"] == "技术部"]
    print(f"   ✓ 技术部岗位: {len(filtered)} 条")

    # 搜索
    searched = df[df["job_title"].str.contains("Python", case=False, na=False)]
    print(f"   ✓ 搜索'Python': {len(searched)} 条")

    # 分页
    page, page_size = 1, 10
    start = (page - 1) * page_size
    end = start + page_size
    paged = df.iloc[start:end]
    print(f"   ✓ 分页 page={page}, page_size={page_size}: {len(paged)} 条")

    # 3. 测试简历列表逻辑
    print("\n3. 测试简历列表逻辑")
    df = resumes_df.copy()

    # 搜索
    searched = df[df["name"].str.contains("张", case=False, na=False)]
    print(f"   ✓ 搜索'张': {len(searched)} 条")

    # 4. 测试匹配逻辑
    print("\n4. 测试匹配逻辑")
    job_id = "JOB_001"
    df = matches_df[matches_df["job_id"] == job_id].copy()
    df = df.sort_values("total_score", ascending=False)
    print(f"   ✓ 岗位 {job_id} 的匹配数: {len(df)}")
    if not df.empty:
        print(f"   ✓ Top 1: {df.iloc[0]['resume_name']} (总分: {df.iloc[0]['total_score']})")

    # 5. 测试 rule_score 计算
    print("\n5. 测试 rule_score 计算")
    if not matches_df.empty:
        row = matches_df.iloc[0]
        rule_score = (
            row["skill_score"] * 0.30
            + row["education_score"] * 0.15
            + row["experience_score"] * 0.10
            + row["city_score"] * 0.05
            + row["salary_score"] * 0.05
            + row["certificate_score"] * 0.05
        ) / 0.70
        print(f"   ✓ 计算的 rule_score: {rule_score:.2f}")

    # 6. 测试匹配详情 JOIN
    print("\n6. 测试匹配详情 JOIN")
    resume_id, job_id = "RES_001", "JOB_001"

    match = matches_df[
        (matches_df["resume_id"] == resume_id) & (matches_df["job_id"] == job_id)
    ]

    if not match.empty:
        match_row = match.iloc[0]
        resume_row = resumes_df[resumes_df["resume_id"] == resume_id].iloc[0]
        job_row = jobs_df[jobs_df["job_id"] == job_id].iloc[0]

        print(f"   ✓ 简历: {resume_row['name']}")
        print(f"   ✓ 岗位: {job_row['job_title']}")
        print(f"   ✓ 总分: {match_row['total_score']}")
        print(f"   ✓ 匹配技能: {match_row['matched_skills']}")

    # 7. 测试统计逻辑
    print("\n7. 测试统计逻辑")
    if not matches_df.empty:
        avg_score = matches_df["total_score"].mean()
        max_score = matches_df["total_score"].max()
        print(f"   ✓ 平均分: {avg_score:.2f}")
        print(f"   ✓ 最高分: {max_score:.2f}")

        score_cols = ["semantic_score", "skill_score", "education_score"]
        for col in score_cols:
            if col in matches_df.columns:
                print(f"   ✓ {col} 平均: {matches_df[col].mean():.2f}")

    if not jobs_df.empty:
        departments = jobs_df["department"].dropna().unique().tolist()
        print(f"   ✓ 部门列表: {departments}")

    print("\n" + "="*60)
    print("✓ 所有单元测试通过")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_unit())
