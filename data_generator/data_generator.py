import asyncio
import csv
import json
import logging
import os
import random
import re
import subprocess
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("data_generator")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
GENERATION_INTERVAL = float(os.getenv("GENERATION_INTERVAL", "10"))
RESUME_INTERVAL = float(os.getenv("RESUME_INTERVAL", str(GENERATION_INTERVAL)))
JOB_INTERVAL = float(os.getenv("JOB_INTERVAL", str(GENERATION_INTERVAL)))
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "60"))
MAX_CONCURRENCY = 4
MAX_RETRIES = 2
REQUEST_TIMEOUT = 60.0
HDFS_BASE_PATH = "/resume_matching/raw"

RESUME_FIELDS = [
    "resume_id",
    "name",
    "gender",
    "age",
    "education",
    "school",
    "major",
    "years_experience",
    "skills",
    "certifications",
    "work_history",
    "expected_salary",
    "location",
    "contact",
]

JOB_FIELDS = [
    "job_id",
    "job_title",
    "department",
    "location",
    "education_required",
    "experience_required",
    "skills_required",
    "skills_preferred",
    "salary_range",
    "job_description",
    "responsibilities",
    "requirements",
]

SKILL_POOL = (
    "Python, SQL, Excel, Pandas, NumPy, Spark, Hadoop, Hive, Flink, Linux, "
    "Java, Spring, MySQL, Tableau, PowerBI, Machine Learning, Data Analysis, "
    "Data Visualization, ETL, Docker"
)

CITY_POOL = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆",
    "苏州", "天津", "长沙", "郑州", "青岛", "合肥", "南昌", "福州", "厦门", "济南",
    "大连", "宁波", "东莞", "昆明", "沈阳", "贵阳", "南宁", "石家庄", "哈尔滨", "太原",
]

SURNAME_POOL = [
    "王", "李", "张", "刘", "陈", "杨", "黄", "赵", "吴", "周",
    "徐", "孙", "马", "朱", "胡", "林", "郭", "何", "高", "罗",
    "郑", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹",
    "彭", "曾", "肖", "田", "董", "袁", "潘", "蒋", "蔡", "叶",
]

JOB_DIRECTIONS = [
    "数据分析", "大数据开发", "Python 开发", "Java 后端", "数据可视化", "机器学习",
]

EDUCATION_POOL = ["大专", "本科", "硕士", "博士"]

RESUME_PROMPT = f"""生成一条用于教学项目“简历-岗位匹配系统”的中文简历脏数据。

只生成一个 JSON 对象，禁止返回数组、Markdown 代码块或解释文字。
JSON 必须严格包含且只包含以下字段：
{json.dumps(RESUME_FIELDS, ensure_ascii=False)}

字段要求：
- resume_id：例如 RES_001；允许 3%-5% 概率与常见编号重复，5%-10% 概率为空。
- name：中文姓名，可少量带“同学”“先生”等多余后缀作为噪声。
- gender：男或女，允许少量为空。
- age：年龄；允许少量异常值，如 -3、88。
- education：大专、本科、硕士、博士；允许“本科学历”“本科及以上”等不统一写法。
- school：毕业院校。
- major：专业。
- years_experience：工作年限；允许 0、1、“一年”“3年以上”等写法。
- skills：技能列表，使用英文逗号分隔。
- certifications：证书列表，使用英文逗号分隔，可为空。
- work_history：工作或项目经历；允许少量 HTML、多余空格、感叹号等噪声。
- expected_salary：期望年薪，单位为万/年；允许异常值 0、999。
- location：期望城市；同一城市可用“城市名”“城市名+市”“省名+城市名”等不统一写法。
- contact：联系方式。

岗位方向覆盖数据分析、大数据开发、Python 开发、Java 后端、数据可视化、机器学习。
技能从以下技能池中合理选择，并允许 py、python、PYTHON、Apache Spark、pyspark、数据分析、数据统计等别名：
{SKILL_POOL}

所有字段必须存在；缺失数据使用空字符串或 null 表示。"""

JOB_PROMPT = f"""生成一条用于教学项目“简历-岗位匹配系统”的中文岗位脏数据。

只生成一个 JSON 对象，禁止返回数组、Markdown 代码块或解释文字。
JSON 必须严格包含且只包含以下字段：
{json.dumps(JOB_FIELDS, ensure_ascii=False)}

字段要求：
- job_id：例如 JOB_001；允许 3%-5% 概率与常见编号重复，5%-10% 概率为空。
- job_title：岗位名称。
- department：所属部门。
- location：工作城市；同一城市可用“城市名”“城市名+市”“省名+城市名”等不统一写法。
- education_required：最低学历；允许“本科”“本科及以上”“硕士”等写法或为空。
- experience_required：最低经验；允许 0、1、“1-3年”“三年以上”等写法。
- skills_required：必备技能，使用英文逗号分隔。
- skills_preferred：加分技能，使用英文逗号分隔，可为空。
- salary_range：年薪范围，例如“8-12万/年”。
- job_description：岗位详细描述；允许少量 HTML、多余空格、感叹号等噪声。
- responsibilities：主要职责。
- requirements：具体要求。

岗位方向以数据分析、大数据开发、Python 开发、Java 后端、数据可视化、机器学习为主。
技能从以下技能池中合理选择，并允许 py、python、Apache Spark、pyspark、数据分析、数据统计等别名：
{SKILL_POOL}

所有字段必须存在；缺失数据使用空字符串或 null 表示。"""

is_generating = False
loop_seq = 0
generation_task: asyncio.Task | None = None
inflight_tasks: set = set()
resume_buffer: List[Dict] = []
job_buffer: List[Dict] = []
stats = {"resumes": 0, "jobs": 0, "last_flush": None, "started_at": None}
recent_resumes: List[Dict] = []
recent_jobs: List[Dict] = []
request_semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
    try:
        yield
    finally:
        await http_client.aclose()
        http_client = None


app = FastAPI(title="Resume-Job Data Generator", lifespan=lifespan)


class GeneratorControl(BaseModel):
    action: str
    resume_interval_seconds: float | None = None
    job_interval_seconds: float | None = None
    flush_interval_seconds: float | None = None


def parse_json_object(content: str, required_fields: List[str]) -> Dict:
    """解析模型返回，并确保结果是符合字段约定的单个对象。"""
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        starts = [index for index in (text.find("{"), text.find("[")) if index >= 0]
        if not starts:
            raise ValueError("模型返回中未找到 JSON")
        data, _ = decoder.raw_decode(text[min(starts):])

    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError(f"期望单个 JSON 对象，实际数组长度={len(data)}")
        data = data[0]

    if not isinstance(data, dict):
        raise ValueError(f"期望 JSON 对象，实际类型={type(data).__name__}")

    missing = [field for field in required_fields if field not in data]
    extra = [field for field in data if field not in required_fields]
    if missing or extra:
        raise ValueError(f"JSON 字段不匹配 | missing={missing} | extra={extra}")

    return {field: data[field] for field in required_fields}


async def call_openai(prompt: str, data_type: str) -> str:
    """调用 OpenAI 兼容 API，限制并发并对临时错误重试。"""
    if http_client is None:
        raise RuntimeError("HTTP client 尚未初始化")

    request_id = uuid.uuid4().hex[:8]
    messages = [{"role": "user", "content": prompt}]

    async with request_semaphore:
        for attempt in range(MAX_RETRIES + 1):
            logger.info(
                "模型请求开始 | request_id=%s | type=%s | model=%s | attempt=%s",
                request_id,
                data_type,
                OPENAI_MODEL,
                attempt + 1,
            )
            try:
                response = await http_client.post(
                    f"{OPENAI_API_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": OPENAI_MODEL,
                        "messages": messages,
                        "temperature": 0.9,
                    },
                )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            "模型请求重试 | request_id=%s | status=%s | attempt=%s",
                            request_id,
                            response.status_code,
                            attempt + 1,
                        )
                        await asyncio.sleep(2 ** attempt)
                        continue
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                logger.info(
                    "模型请求成功 | request_id=%s | type=%s | status=%s",
                    request_id,
                    data_type,
                    response.status_code,
                )
                logger.info("模型返回数据 | request_id=%s | %s", request_id, content)
                return content
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as exc:
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "模型请求重试 | request_id=%s | error_type=%s | attempt=%s",
                        request_id,
                        type(exc).__name__,
                        attempt + 1,
                    )
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.exception(
                    "模型请求失败 | request_id=%s | error_type=%s",
                    request_id,
                    type(exc).__name__,
                )
                raise
            except Exception as exc:
                logger.exception(
                    "模型请求失败 | request_id=%s | error_type=%s",
                    request_id,
                    type(exc).__name__,
                )
                raise

    raise RuntimeError("模型请求重试耗尽")


async def generate_record(prompt: str, data_type: str, fields: List[str], hint: str = "") -> Dict:
    nonce = uuid.uuid4().hex[:8].upper()
    prompt_with_nonce = (
        f"{prompt}\n本次生成随机标识为 {nonce}。"
        f"除少量故意重复或缺失样本外，{fields[0]} 应结合该标识生成不同编号。"
    )
    if hint:
        prompt_with_nonce = f"{prompt_with_nonce}\n{hint}"
    content = await call_openai(prompt_with_nonce, data_type)
    try:
        record = parse_json_object(content, fields)
    except Exception as exc:
        logger.error(
            "模型数据解析失败 | type=%s | error_type=%s | error=%s | raw=%s",
            data_type,
            type(exc).__name__,
            exc,
            content,
        )
        raise
    logger.info("模型数据解析成功 | type=%s | id=%s", data_type, record[fields[0]])
    return record


def build_resume_hint() -> str:
    return (
        "本次简历请尽量贴合以下设定生成（仍保留上面要求的少量缺失/异常/不统一写法）："
        f"姓氏倾向「{random.choice(SURNAME_POOL)}」，"
        f"期望城市「{random.choice(CITY_POOL)}」，"
        f"岗位方向「{random.choice(JOB_DIRECTIONS)}」，"
        f"年龄约 {random.randint(22, 45)} 岁，"
        f"学历「{random.choice(EDUCATION_POOL)}」，"
        f"工作年限约 {random.randint(0, 12)} 年，"
        f"期望年薪约 {random.randint(8, 50)} 万。"
    )


def build_job_hint() -> str:
    salary_low = random.randint(8, 30)
    salary_high = salary_low + random.randint(4, 25)
    return (
        "本次岗位请尽量贴合以下设定生成（仍保留上面要求的少量缺失/异常/不统一写法）："
        f"工作城市「{random.choice(CITY_POOL)}」，"
        f"岗位方向「{random.choice(JOB_DIRECTIONS)}」，"
        f"最低学历「{random.choice(EDUCATION_POOL)}」，"
        f"最低经验约 {random.randint(0, 8)} 年，"
        f"年薪范围约 {salary_low}-{salary_high} 万/年。"
    )


async def generate_resume() -> Dict:
    return await generate_record(RESUME_PROMPT, "resume", RESUME_FIELDS, build_resume_hint())


async def generate_job() -> Dict:
    return await generate_record(JOB_PROMPT, "job", JOB_FIELDS, build_job_hint())


def write_to_hdfs(data: List[Dict], path: str, fieldnames: List[str]) -> None:
    """以标准 CSV 写入临时文件并推送到 HDFS。"""
    if not data:
        return

    # 下游 Spark Streaming 按物理行读取 CSV（未开 multiLine），字段内换行会撕裂记录
    rows = [
        {
            key: re.sub(r"[\r\n]+", " ", value) if isinstance(value, str) else value
            for key, value in row.items()
        }
        for row in data
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.csv"
    target = f"{path}/{filename}"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".csv",
        delete=False,
    ) as file:
        local_file = file.name
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    logger.info("HDFS 推送开始 | records=%s | target=%s", len(data), target)
    try:
        subprocess.run(["hdfs", "dfs", "-put", local_file, target], check=True)
        logger.info("HDFS 推送成功 | records=%s | target=%s", len(data), target)
    except Exception as exc:
        logger.exception(
            "HDFS 推送失败 | records=%s | target=%s | error_type=%s",
            len(data),
            target,
            type(exc).__name__,
        )
        raise
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)


async def flush_buffers() -> None:
    global resume_buffer, job_buffer, stats

    if resume_buffer:
        write_to_hdfs(resume_buffer, f"{HDFS_BASE_PATH}/resumes", RESUME_FIELDS)
        stats["resumes"] += len(resume_buffer)
        resume_buffer = []

    if job_buffer:
        write_to_hdfs(job_buffer, f"{HDFS_BASE_PATH}/jobs", JOB_FIELDS)
        stats["jobs"] += len(job_buffer)
        job_buffer = []

    stats["last_flush"] = datetime.now().isoformat()


def _spawn_generation(data_type: str, seq: int) -> None:
    task = asyncio.create_task(_generate_into_buffer(data_type, seq))
    inflight_tasks.add(task)
    task.add_done_callback(inflight_tasks.discard)


async def _generate_into_buffer(data_type: str, seq: int) -> None:
    try:
        record = await (generate_resume() if data_type == "resume" else generate_job())
    except Exception as exc:
        logger.error(
            "数据生成失败 | type=%s | error_type=%s | error=%r",
            data_type,
            type(exc).__name__,
            exc,
        )
        return

    if seq != loop_seq:
        logger.info("生成器已停止，丢弃在途数据 | type=%s", data_type)
        return

    if data_type == "resume":
        resume_buffer.append(record)
        recent_resumes.insert(0, record)
        del recent_resumes[5:]
    else:
        job_buffer.append(record)
        recent_jobs.insert(0, record)
        del recent_jobs[5:]


async def generation_loop(seq: int) -> None:
    last_flush = time.time()
    last_resume = 0.0
    last_job = 0.0

    while seq == loop_seq:
        try:
            now = time.time()
            spawned = []
            if now - last_resume >= RESUME_INTERVAL:
                _spawn_generation("resume", seq)
                spawned.append("resume")
                last_resume = now
            if now - last_job >= JOB_INTERVAL:
                _spawn_generation("job", seq)
                spawned.append("job")
                last_job = now
            if spawned:
                logger.info("数据生成批次开始 | tasks=%s", spawned)

            if time.time() - last_flush >= FLUSH_INTERVAL:
                await flush_buffers()
                last_flush = time.time()

            await asyncio.sleep(1)
        except Exception as exc:
            logger.exception(
                "生成循环错误 | error_type=%s | error=%s",
                type(exc).__name__,
                exc,
            )
            await asyncio.sleep(5)


@app.post("/control")
async def control_generator(ctrl: GeneratorControl):
    global is_generating, loop_seq, generation_task
    global RESUME_INTERVAL, JOB_INTERVAL, FLUSH_INTERVAL

    if ctrl.action == "start":
        if is_generating:
            raise HTTPException(400, "生成器已在运行")
        if ctrl.resume_interval_seconds is not None:
            RESUME_INTERVAL = max(1.0, ctrl.resume_interval_seconds)
        if ctrl.job_interval_seconds is not None:
            JOB_INTERVAL = max(1.0, ctrl.job_interval_seconds)
        if ctrl.flush_interval_seconds is not None:
            FLUSH_INTERVAL = max(1.0, ctrl.flush_interval_seconds)
        loop_seq += 1
        is_generating = True
        stats["started_at"] = time.time()
        generation_task = asyncio.create_task(generation_loop(loop_seq))
        return {"status": "started", "config": get_config()}

    if ctrl.action == "stop":
        if not is_generating:
            raise HTTPException(400, "生成器未运行")
        is_generating = False
        loop_seq += 1
        for task in list(inflight_tasks):
            task.cancel()
        if generation_task is not None:
            await generation_task
            generation_task = None
        await flush_buffers()
        return {"status": "stopped", "stats": stats}

    raise HTTPException(400, "无效操作")


def get_config() -> Dict:
    return {
        "resume_interval_seconds": RESUME_INTERVAL,
        "job_interval_seconds": JOB_INTERVAL,
        "flush_interval_seconds": FLUSH_INTERVAL,
    }


@app.get("/status")
async def get_status():
    elapsed_minutes = 0
    if stats.get("started_at"):
        elapsed_minutes = max((time.time() - float(stats["started_at"])) / 60, 1 / 60)
    return {
        "running": is_generating,
        "is_generating": is_generating,
        "stats": stats,
        "total_resumes": stats["resumes"],
        "total_jobs": stats["jobs"],
        "buffer_size": {
            "resumes": len(resume_buffer),
            "jobs": len(job_buffer),
        },
        "last_flush_time": stats["last_flush"],
        "generation_rate": {
            "resumes_per_minute": round((stats["resumes"] + len(resume_buffer)) / elapsed_minutes, 2) if is_generating else 0,
            "jobs_per_minute": round((stats["jobs"] + len(job_buffer)) / elapsed_minutes, 2) if is_generating else 0,
        },
        "recent_resumes": recent_resumes,
        "recent_jobs": recent_jobs,
        "config": get_config(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
