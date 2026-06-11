from fastapi import APIRouter, HTTPException, Query

from services.hdfs_reader import get_cached_dataframe

router = APIRouter(prefix="/api", tags=["matches"])


def calc_rule_score(row) -> float:
    """计算规则分数"""
    return round(
        (
            row["skill_score"] * 0.30
            + row["education_score"] * 0.15
            + row["experience_score"] * 0.10
            + row["city_score"] * 0.05
            + row["salary_score"] * 0.05
            + row["certificate_score"] * 0.05
        )
        / 0.70,
        4,
    )


@router.get("/jobs/{job_id}/matches")
async def get_job_matches(
    job_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取岗位匹配的简历"""
    jobs_df = await get_cached_dataframe("jobs")
    matches_df = await get_cached_dataframe("matches")

    if jobs_df.empty or job_id not in jobs_df["job_id"].values:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if matches_df.empty:
        job_info = jobs_df[jobs_df["job_id"] == job_id].iloc[0]
        return {
            "job_id": job_id,
            "job_title": job_info.get("job_title", ""),
            "total_matches": 0,
            "matches": [],
        }

    # 筛选并排序
    df = matches_df[matches_df["job_id"] == job_id].copy()
    df = df.sort_values("total_score", ascending=False)

    # 计算 rule_score
    df["rule_score"] = df.apply(calc_rule_score, axis=1)

    total = len(df)
    items = df.iloc[offset : offset + limit].fillna("").to_dict("records")

    job_info = jobs_df[jobs_df["job_id"] == job_id].iloc[0]

    return {
        "job_id": job_id,
        "job_title": job_info.get("job_title", ""),
        "total_matches": total,
        "matches": items,
    }


@router.get("/resumes/{resume_id}/recommendations")
async def get_resume_recommendations(
    resume_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取简历推荐的岗位"""
    resumes_df = await get_cached_dataframe("resumes")
    matches_df = await get_cached_dataframe("matches")

    if resumes_df.empty or resume_id not in resumes_df["resume_id"].values:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found")

    if matches_df.empty:
        resume_info = resumes_df[resumes_df["resume_id"] == resume_id].iloc[0]
        return {
            "resume_id": resume_id,
            "resume_name": resume_info.get("name", ""),
            "total_recommendations": 0,
            "recommendations": [],
        }

    # 筛选并排序
    df = matches_df[matches_df["resume_id"] == resume_id].copy()
    df = df.sort_values("total_score", ascending=False)

    # 计算 rule_score
    df["rule_score"] = df.apply(calc_rule_score, axis=1)

    total = len(df)
    items = df.iloc[offset : offset + limit].fillna("").to_dict("records")

    resume_info = resumes_df[resumes_df["resume_id"] == resume_id].iloc[0]

    return {
        "resume_id": resume_id,
        "resume_name": resume_info.get("name", ""),
        "total_recommendations": total,
        "recommendations": items,
    }


@router.get("/matches/{resume_id}/{job_id}")
async def get_match_detail(resume_id: str, job_id: str):
    """获取匹配详情"""
    resumes_df = await get_cached_dataframe("resumes")
    jobs_df = await get_cached_dataframe("jobs")
    matches_df = await get_cached_dataframe("matches")

    if resumes_df.empty or resume_id not in resumes_df["resume_id"].values:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found")

    if jobs_df.empty or job_id not in jobs_df["job_id"].values:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # 查找匹配记录
    match = matches_df[
        (matches_df["resume_id"] == resume_id) & (matches_df["job_id"] == job_id)
    ]

    if match.empty:
        raise HTTPException(
            status_code=404, detail=f"Match not found for resume {resume_id} and job {job_id}"
        )

    match_row = match.iloc[0]
    resume_row = resumes_df[resumes_df["resume_id"] == resume_id].iloc[0]
    job_row = jobs_df[jobs_df["job_id"] == job_id].iloc[0]

    # 提取分数
    scores = {
        "total_score": float(match_row.get("total_score", 0)),
        "semantic_score": float(match_row.get("semantic_score", 0)),
        "tfidf_score": float(match_row.get("tfidf_score", 0)),
        "word2vec_score": float(match_row.get("word2vec_score", 0)),
        "rule_score": calc_rule_score(match_row),
        "skill_score": float(match_row.get("skill_score", 0)),
        "education_score": float(match_row.get("education_score", 0)),
        "experience_score": float(match_row.get("experience_score", 0)),
        "city_score": float(match_row.get("city_score", 0)),
        "salary_score": float(match_row.get("salary_score", 0)),
        "certificate_score": float(match_row.get("certificate_score", 0)),
    }

    # 提取匹配和缺失技能
    matched_skills_str = match_row.get("matched_skills", "")
    missing_skills_str = match_row.get("missing_skills", "")
    matched_skills = [s for s in str(matched_skills_str).split("|") if s]
    missing_skills = [s for s in str(missing_skills_str).split("|") if s]

    return {
        "resume": resume_row.fillna("").to_dict(),
        "job": job_row.fillna("").to_dict(),
        "scores": scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "reason": match_row.get("reason", ""),
    }
