import asyncio
import time


class HDFSCache:
    """HDFS DataFrame 缓存管理"""

    def __init__(self, ttl: int = 60):
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._locks = {}

    async def get(self, key: str, fetch_func):
        """获取缓存数据，过期时重新加载"""
        now = time.monotonic()

        # 快速路径：缓存有效
        if key in self._cache and now - self._timestamps.get(key, 0) < self.ttl:
            return self._cache[key]

        # 慢路径：需要加载
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # 双重检查：可能其他协程已经加载
            now = time.monotonic()
            if key in self._cache and now - self._timestamps.get(key, 0) < self.ttl:
                return self._cache[key]

            # 执行加载
            data = await fetch_func()
            self._cache[key] = data
            self._timestamps[key] = time.monotonic()
            return data

    def clear(self, key: str = None):
        """清理缓存"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()
