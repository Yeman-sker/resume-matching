import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/generator", tags=["generator"])


@router.post("/start")
async def start_generator():
    """启动数据生成器"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:8000/control", json={"action": "start"}
            )
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Data generator service unavailable: {str(e)}"
        )


@router.post("/stop")
async def stop_generator():
    """停止数据生成器"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:8000/control", json={"action": "stop"}
            )
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Data generator service unavailable: {str(e)}"
        )
