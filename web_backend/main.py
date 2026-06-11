from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import asyncio
import time
from datetime import datetime

app = FastAPI(title="简历匹配系统 - Web 后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COUNT_CACHE_TTL = 30
count_cache = {"updated_at": 0.0, "values": (0, 0, 0)}
count_cache_lock = asyncio.Lock()


def is_process_running(pattern: str) -> bool:
    result = subprocess.run(
        ["pgrep", "-f", pattern],
        capture_output=True,
        timeout=3,
    )
    return result.returncode == 0


def count_hdfs_csv_rows(path: str, header_first_column: str) -> int:
    try:
        result = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    f"hdfs dfs -cat '{path}/part-*.csv' 2>/dev/null "
                    f"| awk -F, '$1 != \"{header_first_column}\" && $1 != \"\" "
                    "{count++} END {print count+0}'"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return int(result.stdout.strip() or 0)
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0
    return 0


async def get_hdfs_record_counts():
    now = time.monotonic()
    if now - count_cache["updated_at"] < COUNT_CACHE_TTL:
        return count_cache["values"]

    async with count_cache_lock:
        now = time.monotonic()
        if now - count_cache["updated_at"] < COUNT_CACHE_TTL:
            return count_cache["values"]

        values = await asyncio.gather(
            asyncio.to_thread(
                count_hdfs_csv_rows,
                "/resume_matching/processed/resumes",
                "resume_id",
            ),
            asyncio.to_thread(
                count_hdfs_csv_rows,
                "/resume_matching/processed/jobs",
                "job_id",
            ),
            asyncio.to_thread(
                count_hdfs_csv_rows,
                "/resume_matching/output/matches",
                "certificate_score",
            ),
        )
        count_cache["values"] = tuple(values)
        count_cache["updated_at"] = time.monotonic()
        return count_cache["values"]


async def get_system_status():
    total_resumes, total_jobs, total_matches = await get_hdfs_record_counts()
    data_generator_running, streaming_resumes_running, streaming_jobs_running, batch_running = (
        await asyncio.gather(
            asyncio.to_thread(is_process_running, "[d]ata_generator.py"),
            asyncio.to_thread(is_process_running, "[s]treaming_resumes.py"),
            asyncio.to_thread(is_process_running, "[s]treaming_jobs.py"),
            asyncio.to_thread(
                is_process_running,
                "[b]atch_scheduler.py|[b]atch_job.py",
            ),
        )
    )

    return {
        "data_generator_running": data_generator_running,
        "streaming_running": streaming_resumes_running and streaming_jobs_running,
        "batch_running": batch_running,
        "total_resumes": total_resumes,
        "total_jobs": total_jobs,
        "total_matches": total_matches,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/")
def root():
    return {"message": "简历匹配系统 - Web 后端 API"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            status = await get_system_status()
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
