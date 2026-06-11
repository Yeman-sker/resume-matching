import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/generator", tags=["generator"])


class GeneratorConfig(BaseModel):
    resume_interval_seconds: int | None = None
    job_interval_seconds: int | None = None
    flush_interval_seconds: int | None = None


def normalize_status(data: dict) -> dict:
    stats = data.get("stats", {})
    generated = data.get("generated", {})
    rate = data.get("generation_rate", {})
    return {
        "running": bool(data.get("running", data.get("is_generating", False))),
        "total_resumes": int(data.get("total_resumes", generated.get("resumes", stats.get("resumes", 0)) or 0)),
        "total_jobs": int(data.get("total_jobs", generated.get("jobs", stats.get("jobs", 0)) or 0)),
        "buffer_size": data.get("buffer_size", {"resumes": 0, "jobs": 0}),
        "last_flush_time": data.get("last_flush_time", stats.get("last_flush") or ""),
        "generation_rate": {
            "resumes_per_minute": float(rate.get("resumes_per_minute", 0) or 0),
            "jobs_per_minute": float(rate.get("jobs_per_minute", 0) or 0),
        },
        "recent_resumes": data.get("recent_resumes", []),
        "recent_jobs": data.get("recent_jobs", []),
    }


@router.post("/start")
async def start_generator(config: GeneratorConfig | None = None):
    """启动数据生成器"""
    payload = {"action": "start"}
    if config:
        payload.update({key: value for key, value in config.model_dump().items() if value is not None})
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post("http://localhost:8000/control", json=payload)
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
        # stop 内部会等生成循环退出并执行一次 HDFS flush，5 秒不够
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/control", json={"action": "stop"}
            )
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Data generator service unavailable: {str(e)}"
        )


@router.get("/status")
async def get_generator_status():
    """查询数据生成器状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/status")
            response.raise_for_status()
            return normalize_status(response.json())
    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=503, detail=f"Data generator service unavailable: {str(e)}"
        )
