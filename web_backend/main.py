from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import asyncio
from datetime import datetime
from typing import List

app = FastAPI(title="简历匹配系统 - Web 后端")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_hdfs_count(path: str) -> int:
    try:
        result = subprocess.run(
            ["hdfs", "dfs", "-count", path],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            return int(parts[2]) if len(parts) > 2 else 0
    except:
        pass
    return 0

async def get_system_status():
    total_resumes = await get_hdfs_count("/resume_matching/processed/resumes")
    total_jobs = await get_hdfs_count("/resume_matching/processed/jobs")
    total_matches = await get_hdfs_count("/resume_matching/output/matches")

    return {
        "data_generator_running": False,
        "streaming_running": False,
        "batch_running": False,
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
