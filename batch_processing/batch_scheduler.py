import os
import subprocess
import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_ID = "batch_job"
JOB_TIMEOUT_SECONDS = 300
# 与 batch_job.py 的 EXIT_CODE_SKIPPED 保持一致
EXIT_CODE_SKIPPED = 3
LOG_MAX_CHARS = 8000

app = FastAPI(title="简历匹配系统 - 批处理调度器")
scheduler = BackgroundScheduler()

state_lock = threading.Lock()
state = {
    "running": False,
    "current_run": None,
    "last_run": None,
    "last_run_log": "",
    "schedule_paused": False,
}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def try_acquire(trigger: str) -> bool:
    """原子地占用「运行中」槽位，已有任务在跑则返回 False"""
    with state_lock:
        if state["running"]:
            return False
        state["running"] = True
        state["current_run"] = {"trigger": trigger, "started_at": now_str()}
        return True


def execute_batch_job(trigger: str):
    """运行 spark-submit 并记录结果，调用前必须先 try_acquire 成功"""
    started = datetime.now()
    result_name = "success"
    error = ""
    log = ""
    try:
        proc = subprocess.run(
            ["spark-submit", "--master", "local[*]", "--driver-memory", "4g", "batch_job.py"],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=JOB_TIMEOUT_SECONDS,
        )
        log = proc.stdout or ""
        if proc.returncode == EXIT_CODE_SKIPPED:
            result_name = "skipped"
        elif proc.returncode != 0:
            result_name = "failed"
            error = (proc.stderr or "")[-2000:]
    except subprocess.TimeoutExpired:
        result_name = "failed"
        error = f"任务超时（{JOB_TIMEOUT_SECONDS} 秒）"
    except Exception as e:
        result_name = "failed"
        error = str(e)
    finished = datetime.now()
    with state_lock:
        state["running"] = False
        state["current_run"] = None
        state["last_run"] = {
            "trigger": trigger,
            "started_at": started.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished - started).total_seconds(), 1),
            "result": result_name,
            "error": error,
        }
        state["last_run_log"] = log[-LOG_MAX_CHARS:]
    print(f"[{finished}] 批处理任务结束：trigger={trigger} result={result_name}")
    if error:
        print(f"错误: {error}")


def run_scheduled():
    if not try_acquire("scheduled"):
        print(f"[{datetime.now()}] 上一个批处理任务仍在运行，跳过本轮定时触发")
        return
    print(f"[{datetime.now()}] 定时触发批处理任务...")
    execute_batch_job("scheduled")


@app.post("/trigger")
def trigger_job():
    """手动触发批处理任务（训练+匹配），立即返回"""
    if not try_acquire("manual"):
        raise HTTPException(status_code=409, detail="批处理任务正在运行中，请稍后再试")
    print(f"[{datetime.now()}] 手动触发批处理任务...")
    threading.Thread(target=execute_batch_job, args=("manual",), daemon=True).start()
    return {"message": "批处理任务已启动", "trigger": "manual"}


@app.get("/status")
def get_status():
    with state_lock:
        snapshot = {
            "running": state["running"],
            "current_run": state["current_run"],
            "last_run": state["last_run"],
            "last_run_log": state["last_run_log"],
            "schedule_paused": state["schedule_paused"],
        }
    job = scheduler.get_job(JOB_ID)
    next_run = job.next_run_time if job else None
    snapshot["next_scheduled_run"] = (
        next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None
    )
    return snapshot


@app.post("/schedule/pause")
def pause_schedule():
    """暂停定时自动触发（手动触发不受影响）"""
    scheduler.pause_job(JOB_ID)
    with state_lock:
        state["schedule_paused"] = True
    return {"message": "自动调度已暂停", "schedule_paused": True}


@app.post("/schedule/resume")
def resume_schedule():
    """恢复定时自动触发"""
    scheduler.resume_job(JOB_ID)
    with state_lock:
        state["schedule_paused"] = False
    return {"message": "自动调度已恢复", "schedule_paused": False}


if __name__ == "__main__":
    import uvicorn

    scheduler.add_job(run_scheduled, "interval", minutes=10, id=JOB_ID)
    scheduler.start()
    print("批处理调度器已启动（每 10 分钟自动运行一次，API 端口 8001）")
    uvicorn.run(app, host="0.0.0.0", port=8001)
