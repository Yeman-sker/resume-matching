import os
import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Resume-Job Data Generator")

# 配置
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HDFS_BASE_PATH = "/resume_matching/raw"
BATCH_SIZE = 20
FLUSH_INTERVAL = 60

# 全局状态
is_generating = False
resume_buffer: List[Dict] = []
job_buffer: List[Dict] = []
stats = {"resumes": 0, "jobs": 0, "last_flush": None}


class GeneratorControl(BaseModel):
    action: str  # start/stop


async def call_openai(prompt: str, system: str = None) -> str:
    """调用 OpenAI 兼容 API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await client.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4", "messages": messages, "temperature": 0.9}
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def write_to_hdfs(data: List[Dict], path: str):
    """写入 HDFS"""
    if not data:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{timestamp}.csv"
    local_file = f"/tmp/{filename}"

    # 写入本地临时文件
    with open(local_file, "w") as f:
        if data:
            keys = data[0].keys()
            f.write(",".join(keys) + "\n")
            for item in data:
                row = [str(item.get(k, "")).replace(",", ";") for k in keys]
                f.write(",".join(row) + "\n")

    # 上传到 HDFS
    subprocess.run(["hdfs", "dfs", "-put", local_file, f"{path}/{filename}"], check=True)
    os.remove(local_file)


async def generate_resume() -> Dict:
    """生成一份简历（含脏数据）"""
    prompt = """生成一份中文求职简历的JSON数据（需包含15%脏数据概率）：
{
  "resume_id": "唯一ID（5%概率为空或重复）",
  "name": "姓名",
  "gender": "性别（男/女/未知，10%概率格式错误如'm'/'f'）",
  "age": "年龄数字（5%概率为字符串'二十五'）",
  "education": "学历（本科/硕士/博士/大专，10%概率为'Bachelor'等英文）",
  "major": "专业",
  "skills": "技能列表，逗号分隔（15%概率包含HTML标签如'<b>Python</b>'）",
  "experience_years": "工作年限（5%概率为'三年经验'等文本）",
  "city": "期望城市（10%概率用英文'Beijing'或缩写'BJ'）",
  "expected_salary": "期望薪资（如'15000-20000'，10%概率格式混乱如'15k~20k'）",
  "certificates": "证书列表，逗号分隔"
}
只返回JSON，不要其他文字。"""

    content = await call_openai(prompt)
    # 提取JSON
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end])


async def generate_job() -> Dict:
    """生成一个岗位（含脏数据）"""
    prompt = """生成一份中文招聘岗位的JSON数据（需包含15%脏数据概率）：
{
  "job_id": "唯一ID（5%概率为空或重复）",
  "title": "岗位名称",
  "company": "公司名称",
  "required_skills": "要求技能，逗号分隔（15%概率包含HTML如'<strong>Java</strong>'）",
  "required_education": "学历要求（本科/硕士/博士/大专，10%概率为'Bachelor'）",
  "required_experience": "经验要求（5%概率为'需要三年'等文本）",
  "city": "工作城市（10%概率用英文或缩写）",
  "salary_range": "薪资范围（如'15000-25000'，10%概率格式混乱）",
  "required_certificates": "要求证书，逗号分隔"
}
只返回JSON，不要其他文字。"""

    content = await call_openai(prompt)
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end])


async def flush_buffers():
    """刷新缓冲区到 HDFS"""
    global resume_buffer, job_buffer, stats

    if resume_buffer:
        write_to_hdfs(resume_buffer, f"{HDFS_BASE_PATH}/resumes")
        stats["resumes"] += len(resume_buffer)
        resume_buffer = []

    if job_buffer:
        write_to_hdfs(job_buffer, f"{HDFS_BASE_PATH}/jobs")
        stats["jobs"] += len(job_buffer)
        job_buffer = []

    stats["last_flush"] = datetime.now().isoformat()


async def generation_loop():
    """持续生成数据"""
    global is_generating
    last_flush = time.time()

    while is_generating:
        try:
            # 并发生成一批数据
            tasks = []
            for _ in range(BATCH_SIZE // 2):
                tasks.append(generate_resume())
                tasks.append(generate_job())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    continue
                if i % 2 == 0:
                    resume_buffer.append(result)
                else:
                    job_buffer.append(result)

            # 定时刷新
            if time.time() - last_flush >= FLUSH_INTERVAL:
                await flush_buffers()
                last_flush = time.time()

        except Exception as e:
            print(f"生成错误: {e}")
            await asyncio.sleep(5)


@app.post("/control")
async def control_generator(ctrl: GeneratorControl):
    """控制数据生成器"""
    global is_generating

    if ctrl.action == "start":
        if is_generating:
            raise HTTPException(400, "生成器已在运行")
        is_generating = True
        asyncio.create_task(generation_loop())
        return {"status": "started"}

    elif ctrl.action == "stop":
        if not is_generating:
            raise HTTPException(400, "生成器未运行")
        is_generating = False
        await flush_buffers()
        return {"status": "stopped", "stats": stats}

    else:
        raise HTTPException(400, "无效操作")


@app.get("/status")
async def get_status():
    """获取生成器状态"""
    return {
        "is_generating": is_generating,
        "stats": stats,
        "buffer_size": {
            "resumes": len(resume_buffer),
            "jobs": len(job_buffer)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
