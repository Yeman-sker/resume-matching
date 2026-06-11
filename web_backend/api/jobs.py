from fastapi import APIRouter, Query

from services.hdfs_reader import get_cached_dataframe

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs")
async def get_jobs(
    department: str = Query(None, description="按部门筛选"),
    search: str = Query(None, description="按岗位名称搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """获取岗位列表"""
    jobs_df = await get_cached_dataframe("jobs")

    if jobs_df.empty:
        return {"total": 0, "page": page, "page_size": page_size, "jobs": []}

    # 筛选
    df = jobs_df.copy()
    if department:
        df = df[df["department"] == department]
    if search:
        df = df[df["job_title"].str.contains(search, case=False, na=False)]

    total = len(df)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items = df.iloc[start:end].fillna("").to_dict("records")

    return {"total": total, "page": page, "page_size": page_size, "jobs": items}
