from fastapi import APIRouter

from services.hdfs_reader import get_cached_dataframe

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
async def get_stats():
    """获取统计数据"""
    matches_df = await get_cached_dataframe("matches")
    jobs_df = await get_cached_dataframe("jobs")
    resumes_df = await get_cached_dataframe("resumes")

    if matches_df.empty:
        return {
            "total_resumes": len(resumes_df),
            "total_jobs": len(jobs_df),
            "total_matches": 0,
            "avg_total_score": 0.0,
            "max_total_score": 0.0,
            "score_distribution": {},
            "departments": jobs_df["department"].dropna().unique().tolist() if not jobs_df.empty else [],
        }

    score_cols = [
        "semantic_score",
        "skill_score",
        "education_score",
        "experience_score",
        "city_score",
        "salary_score",
        "certificate_score",
    ]

    return {
        "total_resumes": len(resumes_df),
        "total_jobs": len(jobs_df),
        "total_matches": len(matches_df),
        "avg_total_score": round(float(matches_df["total_score"].mean()), 2),
        "max_total_score": round(float(matches_df["total_score"].max()), 2),
        "score_distribution": {
            f"{col}_avg": round(float(matches_df[col].mean()), 2)
            for col in score_cols
            if col in matches_df.columns
        },
        "departments": jobs_df["department"].dropna().unique().tolist() if not jobs_df.empty else [],
    }
