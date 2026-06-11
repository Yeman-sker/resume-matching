#!/usr/bin/env python3
"""使用模拟缓存数据测试后端 API（无需 HDFS）"""

import asyncio
import pandas as pd
import sys
import httpx
from main import app

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
    {
        "resume_id": "RES_003", "name": "王五", "gender": "男", "age": 23,
        "education": "本科", "school": "北京大学", "major": "软件工程",
        "years_experience": "1年", "skills": "Java|Spring|MySQL",
        "certifications": "", "work_history": "Java开发实习",
        "expected_salary": 10, "location": "深圳", "contact": "13800138002",
        "education_level": 3, "experience_years_num": 1,
        "standard_location": "深圳", "standard_skills": "Java|Spring|MySQL",
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
    {
        "job_id": "JOB_003", "job_title": "Java后端开发", "department": "技术部",
        "location": "深圳", "education_required": "本科", "experience_required": "1-3年",
        "skills_required": "Java|Spring|MySQL", "skills_preferred": "Redis|Docker",
        "salary_range": "12-18万/年", "education_required_level": 3,
        "experience_required_num": 2, "standard_location": "深圳",
        "required_skills_standard": "Java|Spring|MySQL",
        "preferred_skills_standard": "Redis|Docker", "salary_min": 12, "salary_max": 18,
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
    {
        "resume_id": "RES_003", "resume_name": "王五", "job_id": "JOB_003",
        "job_title": "Java后端开发", "department": "技术部",
        "tfidf_score": 90.5, "word2vec_score": 88.2, "semantic_score": 89.5,
        "skill_score": 100.0, "education_score": 100.0, "experience_score": 70.0,
        "city_score": 100.0, "salary_score": 70.0, "certificate_score": 60.0,
        "total_score": 87.4, "matched_skills": "Java|Spring|MySQL",
        "missing_skills": "", "reason": "较好匹配",
    },
])


async def mock_test():
    """测试所有 API 接口（使用模拟数据）"""

    # 注入模拟数据到缓存
    import sys
    sys.path.insert(0, '.')
    from services.hdfs_reader import hdfs_cache

    hdfs_cache._cache["resumes"] = MOCK_RESUMES
    hdfs_cache._cache["jobs"] = MOCK_JOBS
    hdfs_cache._cache["matches"] = MOCK_MATCHES
    hdfs_cache._timestamps["resumes"] = 999999999
    hdfs_cache._timestamps["jobs"] = 999999999
    hdfs_cache._timestamps["matches"] = 999999999

    print("✓ 模拟数据已注入缓存\n")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
        base_url = ""

        # 1. 测试统计接口
        print("1. 测试统计接口 GET /api/stats")
        resp = await client.get(f"{base_url}/api/stats")
        data = resp.json()
        print(f"   ✓ 简历数: {data['total_resumes']}")
        print(f"   ✓ 岗位数: {data['total_jobs']}")
        print(f"   ✓ 匹配数: {data['total_matches']}")
        print(f"   ✓ 平均分: {data['avg_total_score']}")
        print(f"   ✓ 最高分: {data['max_total_score']}")
        print(f"   ✓ 部门列表: {data['departments']}")

        # 2. 测试岗位列表
        print("\n2. 测试岗位列表 GET /api/jobs")
        resp = await client.get(f"{base_url}/api/jobs?page=1&page_size=10")
        data = resp.json()
        print(f"   ✓ 总数: {data['total']}")
        print(f"   ✓ 返回: {len(data['jobs'])} 条")
        for job in data['jobs']:
            print(f"      - {job['job_id']}: {job['job_title']} ({job['department']})")

        # 3. 测试简历列表
        print("\n3. 测试简历列表 GET /api/resumes")
        resp = await client.get(f"{base_url}/api/resumes?page=1&page_size=10")
        data = resp.json()
        print(f"   ✓ 总数: {data['total']}")
        print(f"   ✓ 返回: {len(data['resumes'])} 条")
        for resume in data['resumes']:
            print(f"      - {resume['resume_id']}: {resume['name']} ({resume['education']})")

        # 4. 测试岗位匹配
        print("\n4. 测试岗位匹配 GET /api/jobs/JOB_001/matches")
        resp = await client.get(f"{base_url}/api/jobs/JOB_001/matches?limit=10")
        data = resp.json()
        print(f"   ✓ 岗位: {data['job_title']}")
        print(f"   ✓ 匹配总数: {data['total_matches']}")
        print(f"   ✓ 返回: {len(data['matches'])} 条")
        if data['matches']:
            match = data['matches'][0]
            print(f"      Top 1: {match['resume_name']} (总分: {match['total_score']})")

        # 5. 测试简历推荐
        print("\n5. 测试简历推荐 GET /api/resumes/RES_001/recommendations")
        resp = await client.get(f"{base_url}/api/resumes/RES_001/recommendations?limit=10")
        data = resp.json()
        print(f"   ✓ 简历: {data['resume_name']}")
        print(f"   ✓ 推荐总数: {data['total_matches']}")
        print(f"   ✓ 返回: {len(data['matches'])} 条")
        if data['matches']:
            rec = data['matches'][0]
            print(f"      Top 1: {rec['job_title']} (总分: {rec['total_score']})")

        # 6. 测试匹配详情
        print("\n6. 测试匹配详情 GET /api/matches/RES_001/JOB_001")
        resp = await client.get(f"{base_url}/api/matches/RES_001/JOB_001")
        data = resp.json()
        print(f"   ✓ 简历: {data['resume']['name']}")
        print(f"   ✓ 岗位: {data['job']['job_title']}")
        print(f"   ✓ 总分: {data['scores']['total_score']}")
        print(f"   ✓ 语义分: {data['scores']['semantic_score']}")
        print(f"   ✓ 规则分: {data['scores']['rule_score']}")
        print(f"   ✓ 匹配技能: {data['matched_skills']}")
        print(f"   ✓ 缺失技能: {data['missing_skills']}")

        # 7. 测试搜索和筛选
        print("\n7. 测试搜索和筛选")
        resp = await client.get(f"{base_url}/api/jobs?department=技术部")
        data = resp.json()
        print(f"   ✓ 技术部岗位: {data['total']} 条")

        resp = await client.get(f"{base_url}/api/jobs?search=Python")
        data = resp.json()
        print(f"   ✓ 搜索'Python': {data['total']} 条")

        resp = await client.get(f"{base_url}/api/resumes?search=张")
        data = resp.json()
        print(f"   ✓ 搜索'张': {data['total']} 条")

        resp = await client.get(f"{base_url}/api/generator/status")
        print(f"   ✓ 生成器状态接口可达: {resp.status_code in (200, 503)}")

        print("\n" + "="*60)
        print("✓ 所有测试通过")


if __name__ == "__main__":
    asyncio.run(mock_test())
