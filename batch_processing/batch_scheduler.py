import time
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

scheduler = BlockingScheduler()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

@scheduler.scheduled_job('interval', minutes=10)
def run_batch_job():
    print(f"[{datetime.now()}] 触发批处理任务...")
    try:
        result = subprocess.run(
            ["spark-submit", "--master", "local[*]", "--driver-memory", "4g", "batch_job.py"],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"批处理任务失败: {e}")

if __name__ == "__main__":
    print("批处理调度器已启动（每 10 分钟运行一次）")
    print("按 Ctrl+C 停止")

    # 立即运行一次
    run_batch_job()

    # 启动定时调度
    scheduler.start()
