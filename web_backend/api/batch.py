import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/batch", tags=["batch"])

BATCH_SERVICE_URL = "http://localhost:8001"


@router.post("/trigger")
async def trigger_batch():
    """手动触发批处理任务（训练+匹配）"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{BATCH_SERVICE_URL}/trigger")
            if response.status_code == 409:
                detail = response.json().get("detail", "批处理任务正在运行中")
                raise HTTPException(status_code=409, detail=detail)
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Batch service unavailable: {str(e)}"
        )


@router.get("/status")
async def get_batch_status():
    """查询批处理任务状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BATCH_SERVICE_URL}/status")
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Batch service unavailable: {str(e)}"
        )


@router.get("/progress")
async def get_batch_progress():
    """查询批处理任务实时进度（运行期间前端高频轮询）"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BATCH_SERVICE_URL}/progress")
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Batch service unavailable: {str(e)}"
        )


@router.post("/schedule/pause")
async def pause_batch_schedule():
    """暂停定时自动触发"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{BATCH_SERVICE_URL}/schedule/pause")
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Batch service unavailable: {str(e)}"
        )


@router.post("/schedule/resume")
async def resume_batch_schedule():
    """恢复定时自动触发"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{BATCH_SERVICE_URL}/schedule/resume")
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Batch service unavailable: {str(e)}"
        )
