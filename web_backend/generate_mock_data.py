#!/usr/bin/env python3
"""生成 Mock 数据用于测试后端 API"""

import asyncio
import csv
import os
import subprocess
import tempfile
from datetime import datetime


def write_hdfs_csv(local_path: str, hdfs_path: str):
    """将本地 CSV 写入 HDFS"""
    subprocess.run(
        ["hdfs", "dfs", "-mkdir", "-p", os.path.dirname(hdfs_path)],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["hdfs", "dfs", "-put", "-f", local_path, hdfs_path],
        check=True,
        capture_output=True,
    )


def generate_mock_data():
    """生成 Mock 测试数据"""
    print("生成 Mock 测试数据...")

    # 生成 3 条简历
    resumes = [
        {
            "resume_id": "RES_001",
            "name": "张三",
            "gender": "男",
            "age": 25,
            "education": "本科",
            "school": "南昌大学",
            "major": "计算机科学",
            "years_experience": "2年",
            "skills": "Python|SQL|Pandas",
            "certifications": "软件设计师",
            "work_history": "曾在ABC公司担任数据分析师",
            "expected_salary": 12,
            "location": "南昌",
            "contact": "13800138000",
            "education_level": 3,
            "experience_years_num": 2,
            "standard_location": "南昌",
            "standard_skills": "Python|SQL|Pandas",
            "skill_items_raw": "Python|SQL|Pandas",
            "certification_items": "软件设计师",
            "tokens": '["Python", "SQL", "数据分析"]',
            "clean_text": "Python SQL 数据分析",
        },
        {
            "resume_id": "RES_002",
            "name": "李四",
            "gender": "女",
            "age": 28,
            "education": "硕士",
            "school": "清华大学",
            "major": "数据科学",
            "years_experience": "3年",
            "skills": "Python|Spark|Hadoop",
            "certifications": "数据分析师",
            "work_history": "大数据工程师",
            "expected_salary": 20,
            "location": "北京",
            "contact": "13800138001",
            "education_level": 4,
            "experience_years_num": 3,
            "standard_location": "北京",
            "standard_skills": "Python|Spark|Hadoop",
            "skill_items_raw": "Python|Spark|Hadoop",
            "certification_items": "数据分析师",
            "tokens": '["Python", "Spark", "大数据"]',
            "clean_text": "Python Spark 大数据",
        },
        {
            "resume_id": "RES_003",
            "name": "王五",
            "gender": "男",
            "age": 23,
            "education": "本科",
            "school": "北京大学",
            "major": "软件工程",
            "years_experience": "1年",
            "skills": "Java|Spring|MySQL",
            "certifications": "",
            "work_history": "Java开发实习",
            "expected_salary": 10,
            "location": "深圳",
            "contact": "13800138002",
            "education_level": 3,
            "experience_years_num": 1,
            "standard_location": "深圳",
            "standard_skills": "Java|Spring|MySQL",
            "skill_items_raw": "Java|Spring|MySQL",
            "certification_items": "",
            "tokens": '["Java", "Spring", "开发"]',
            "clean_text": "Java Spring 开发",
        },
    ]

    # 生成 3 条岗位
    jobs = [
        {
            "job_id": "JOB_001",
            "job_title": "Python数据分析师",
            "department": "技术部",
            "location": "南昌",
            "education_required": "本科",
            "experience_required": "1-3年",
            "skills_required": "Python|SQL|Pandas",
            "skills_preferred": "Spark|Tableau",
            "salary_range": "10-15万/年",
            "job_description": "负责数据分析和报表开发",
            "responsibilities": "数据清洗、分析、可视化",
            "requirements": "本科以上，熟悉Python",
            "education_required_level": 3,
            "experience_required_num": 2,
            "standard_location": "南昌",
            "required_skills_standard": "Python|SQL|Pandas",
            "preferred_skills_standard": "Spark|Tableau",
            "required_skill_items_raw": "Python|SQL|Pandas",
            "preferred_skill_items_raw": "Spark|Tableau",
            "salary_min": 10,
            "salary_max": 15,
            "tokens": '["Python", "数据分析", "SQL"]',
            "clean_text": "Python 数据分析 SQL",
        },
        {
            "job_id": "JOB_002",
            "job_title": "大数据开发工程师",
            "department": "数据部",
            "location": "北京",
            "education_required": "硕士",
            "experience_required": "3年以上",
            "skills_required": "Spark|Hadoop|Hive",
            "skills_preferred": "Flink|Kafka",
            "salary_range": "20-30万/年",
            "job_description": "负责大数据平台开发",
            "responsibilities": "ETL开发、数据仓库建设",
            "requirements": "硕士以上，3年大数据经验",
            "education_required_level": 4,
            "experience_required_num": 3,
            "standard_location": "北京",
            "required_skills_standard": "Spark|Hadoop|Hive",
            "preferred_skills_standard": "Flink|Kafka",
            "required_skill_items_raw": "Spark|Hadoop|Hive",
            "preferred_skill_items_raw": "Flink|Kafka",
            "salary_min": 20,
            "salary_max": 30,
            "tokens": '["Spark", "Hadoop", "大数据"]',
            "clean_text": "Spark Hadoop 大数据",
        },
        {
            "job_id": "JOB_003",
            "job_title": "Java后端开发",
            "department": "技术部",
            "location": "深圳",
            "education_required": "本科",
            "experience_required": "1-3年",
            "skills_required": "Java|Spring|MySQL",
            "skills_preferred": "Redis|Docker",
            "salary_range": "12-18万/年",
            "job_description": "负责后端服务开发",
            "responsibilities": "API开发、数据库设计",
            "requirements": "本科以上，熟悉Java",
            "education_required_level": 3,
            "experience_required_num": 2,
            "standard_location": "深圳",
            "required_skills_standard": "Java|Spring|MySQL",
            "preferred_skills_standard": "Redis|Docker",
            "required_skill_items_raw": "Java|Spring|MySQL",
            "preferred_skill_items_raw": "Redis|Docker",
            "salary_min": 12,
            "salary_max": 18,
            "tokens": '["Java", "Spring", "后端"]',
            "clean_text": "Java Spring 后端",
        },
    ]

    # 生成 9 条匹配结果（3x3 笛卡尔积）
    matches = [
        {
            "resume_id": "RES_001",
            "resume_name": "张三",
            "job_id": "JOB_001",
            "job_title": "Python数据分析师",
            "department": "技术部",
            "tfidf_score": 88.5,
            "word2vec_score": 85.3,
            "semantic_score": 87.2,
            "skill_score": 100.0,
            "education_score": 100.0,
            "experience_score": 100.0,
            "city_score": 100.0,
            "salary_score": 100.0,
            "certificate_score": 100.0,
            "total_score": 95.6,
            "matched_skills": "Python|SQL|Pandas",
            "missing_skills": "",
            "reason": "技能匹配较高，共同技能包括：Pandas、Python、SQL；简历文本与岗位描述方向非常接近；学历满足要求；经验年限满足岗位要求；城市匹配",
        },
        {
            "resume_id": "RES_001",
            "resume_name": "张三",
            "job_id": "JOB_002",
            "job_title": "大数据开发工程师",
            "department": "数据部",
            "tfidf_score": 45.2,
            "word2vec_score": 50.1,
            "semantic_score": 47.1,
            "skill_score": 30.0,
            "education_score": 60.0,
            "experience_score": 70.0,
            "city_score": 50.0,
            "salary_score": 40.0,
            "certificate_score": 100.0,
            "total_score": 48.5,
            "matched_skills": "",
            "missing_skills": "Spark|Hadoop|Hive",
            "reason": "技能匹配偏低，需要补充岗位核心技能；仍缺少技能：Hadoop、Hive、Spark；简历文本与岗位描述存在一定相关性；学历与岗位要求存在差距；经验略低于要求，但差距不大；城市不完全匹配",
        },
        {
            "resume_id": "RES_001",
            "resume_name": "张三",
            "job_id": "JOB_003",
            "job_title": "Java后端开发",
            "department": "技术部",
            "tfidf_score": 30.5,
            "word2vec_score": 35.2,
            "semantic_score": 32.3,
            "skill_score": 0.0,
            "education_score": 100.0,
            "experience_score": 100.0,
            "city_score": 50.0,
            "salary_score": 100.0,
            "certificate_score": 100.0,
            "total_score": 51.7,
            "matched_skills": "",
            "missing_skills": "Java|Spring|MySQL",
            "reason": "技能匹配偏低，需要补充岗位核心技能；仍缺少技能：Java、MySQL、Spring；文本相似度较低；学历满足要求；经验年限满足岗位要求；城市不完全匹配",
        },
        {
            "resume_id": "RES_002",
            "resume_name": "李四",
            "job_id": "JOB_001",
            "job_title": "Python数据分析师",
            "department": "技术部",
            "tfidf_score": 70.2,
            "word2vec_score": 68.5,
            "semantic_score": 69.5,
            "skill_score": 85.0,
            "education_score": 100.0,
            "experience_score": 100.0,
            "city_score": 50.0,
            "salary_score": 40.0,
            "certificate_score": 100.0,
            "total_score": 74.9,
            "matched_skills": "Python",
            "missing_skills": "SQL|Pandas",
            "reason": "技能匹配较高，共同技能包括：Python；仍缺少技能：Pandas、SQL；简历文本与岗位描述方向非常接近；学历满足要求；经验年限满足岗位要求；城市不完全匹配",
        },
        {
            "resume_id": "RES_002",
            "resume_name": "李四",
            "job_id": "JOB_002",
            "job_title": "大数据开发工程师",
            "department": "数据部",
            "tfidf_score": 92.1,
            "word2vec_score": 90.5,
            "semantic_score": 91.4,
            "skill_score": 100.0,
            "education_score": 100.0,
            "experience_score": 100.0,
            "city_score": 100.0,
            "salary_score": 100.0,
            "certificate_score": 100.0,
            "total_score": 97.4,
            "matched_skills": "Spark|Hadoop",
            "missing_skills": "Hive",
            "reason": "技能匹配较高，共同技能包括：Hadoop、Spark；仍缺少技能：Hive；简历文本与岗位描述方向非常接近；学历满足要求；经验年限满足岗位要求；城市匹配",
        },
        {
            "resume_id": "RES_002",
            "resume_name": "李四",
            "job_id": "JOB_003",
            "job_title": "Java后端开发",
            "department": "技术部",
            "tfidf_score": 25.3,
            "word2vec_score": 28.1,
            "semantic_score": 26.5,
            "skill_score": 0.0,
            "education_score": 100.0,
            "experience_score": 100.0,
            "city_score": 50.0,
            "salary_score": 40.0,
            "certificate_score": 100.0,
            "total_score": 45.0,
            "matched_skills": "",
            "missing_skills": "Java|Spring|MySQL",
            "reason": "技能匹配偏低，需要补充岗位核心技能；仍缺少技能：Java、MySQL、Spring；文本相似度较低；学历满足要求；经验年限满足岗位要求；城市不完全匹配",
        },
        {
            "resume_id": "RES_003",
            "resume_name": "王五",
            "job_id": "JOB_001",
            "job_title": "Python数据分析师",
            "department": "技术部",
            "tfidf_score": 35.2,
            "word2vec_score": 38.5,
            "semantic_score": 36.6,
            "skill_score": 0.0,
            "education_score": 100.0,
            "experience_score": 70.0,
            "city_score": 50.0,
            "salary_score": 40.0,
            "certificate_score": 60.0,
            "total_score": 40.0,
            "matched_skills": "",
            "missing_skills": "Python|SQL|Pandas",
            "reason": "技能匹配偏低，需要补充岗位核心技能；仍缺少技能：Pandas、Python、SQL；文本相似度较低；学历满足要求；经验略低于要求，但差距不大；城市不完全匹配",
        },
        {
            "resume_id": "RES_003",
            "resume_name": "王五",
            "job_id": "JOB_002",
            "job_title": "大数据开发工程师",
            "department": "数据部",
            "tfidf_score": 20.1,
            "word2vec_score": 22.5,
            "semantic_score": 21.1,
            "skill_score": 0.0,
            "education_score": 60.0,
            "experience_score": 40.0,
            "city_score": 50.0,
            "salary_score": 40.0,
            "certificate_score": 60.0,
            "total_score": 28.3,
            "matched_skills": "",
            "missing_skills": "Spark|Hadoop|Hive",
            "reason": "技能匹配偏低，需要补充岗位核心技能；仍缺少技能：Hadoop、Hive、Spark；文本相似度较低；学历与岗位要求存在差距；经验年限与岗位要求差距较大；城市不完全匹配",
        },
        {
            "resume_id": "RES_003",
            "resume_name": "王五",
            "job_id": "JOB_003",
            "job_title": "Java后端开发",
            "department": "技术部",
            "tfidf_score": 90.5,
            "word2vec_score": 88.2,
            "semantic_score": 89.5,
            "skill_score": 100.0,
            "education_score": 100.0,
            "experience_score": 70.0,
            "city_score": 100.0,
            "salary_score": 70.0,
            "certificate_score": 60.0,
            "total_score": 87.4,
            "matched_skills": "Java|Spring|MySQL",
            "missing_skills": "",
            "reason": "技能匹配较高，共同技能包括：Java、MySQL、Spring；简历文本与岗位描述方向非常接近；学历满足要求；经验略低于要求，但差距不大；城市匹配",
        },
    ]

    # 写入临时文件并上传到 HDFS
    with tempfile.TemporaryDirectory() as tmpdir:
        # 简历
        resume_csv = os.path.join(tmpdir, "resumes.csv")
        with open(resume_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=resumes[0].keys())
            writer.writeheader()
            writer.writerows(resumes)
        write_hdfs_csv(
            resume_csv,
            f"/resume_matching/processed/resumes/part-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
        )
        print(f"  ✓ 已写入 {len(resumes)} 条简历")

        # 岗位
        job_csv = os.path.join(tmpdir, "jobs.csv")
        with open(job_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
        write_hdfs_csv(
            job_csv,
            f"/resume_matching/processed/jobs/part-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
        )
        print(f"  ✓ 已写入 {len(jobs)} 条岗位")

        # 匹配结果
        match_csv = os.path.join(tmpdir, "matches.csv")
        with open(match_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)
        write_hdfs_csv(
            match_csv,
            f"/resume_matching/output/matches/part-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
        )
        print(f"  ✓ 已写入 {len(matches)} 条匹配结果")

    print("\n✓ Mock 数据生成完成")


if __name__ == "__main__":
    generate_mock_data()
