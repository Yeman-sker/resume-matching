from fastapi import APIRouter, Query

from services.hdfs_reader import get_cached_dataframe

router = APIRouter(prefix="/api", tags=["resumes"])


@router.get("/resumes")
async def get_resumes(
    search: str = Query(None, description="按姓名搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """获取简历列表"""
    resumes_df = await get_cached_dataframe("resumes")

    if resumes_df.empty:
        return {"total": 0, "page": page, "page_size": page_size, "resumes": []}

    # 筛选
    df = resumes_df.copy()
    if search:
        df = df[df["name"].str.contains(search, case=False, na=False)]

    total = len(df)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    items = df.iloc[start:end].fillna("").to_dict("records")

    return {"total": total, "page": page, "page_size": page_size, "resumes": items}
