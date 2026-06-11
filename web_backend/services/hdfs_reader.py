import asyncio
import io
import subprocess

import pandas as pd

from services.cache import HDFSCache

# 全局缓存实例
hdfs_cache = HDFSCache(ttl=60)


def read_hdfs_csv(path: str) -> pd.DataFrame:
    """从 HDFS 读取 CSV 文件"""
    try:
        result = subprocess.run(
            ["hdfs", "dfs", "-cat", f"{path}/part-*.csv"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return pd.DataFrame()
        df = pd.read_csv(
            io.StringIO(result.stdout),
            encoding="utf-8-sig",
            escapechar="\\",
            on_bad_lines="skip",
        )
        valid_id_pattern = r"^(?:(?:JOB|RES)_[A-Z0-9]+(?:[-_][0-9]+)?|[A-Z0-9]{8}(?:[-_][0-9]+)?)$"
        if "job_id" in df.columns:
            df = df[df["job_id"].astype(str).str.match(valid_id_pattern, na=False)]
        if "resume_id" in df.columns:
            df = df[df["resume_id"].astype(str).str.match(valid_id_pattern, na=False)]
        return df
    except (OSError, subprocess.SubprocessError, ValueError, subprocess.TimeoutExpired):
        return pd.DataFrame()


async def get_cached_dataframe(dataset: str) -> pd.DataFrame:
    """获取缓存的 DataFrame"""
    path_map = {
        "resumes": "/resume_matching/processed/resumes",
        "jobs": "/resume_matching/processed/jobs",
        "matches": "/resume_matching/output/matches",
    }

    if dataset not in path_map:
        return pd.DataFrame()

    path = path_map[dataset]
    return await hdfs_cache.get(dataset, lambda: asyncio.to_thread(read_hdfs_csv, path))
