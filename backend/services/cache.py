"""Redis caching service for agent outputs and evaluation results."""

import json
import logging
import redis.asyncio as redis
from typing import Optional, Any
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching for evaluation results and agent outputs."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
            except Exception:
                logger.debug("Redis unavailable, caching disabled")
                self._redis = None
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        try:
            client = await self._get_client()
            if client is None:
                return None
            value = await client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            logger.debug("Cache get failed for key=%s", key, exc_info=True)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set a cached value with TTL in seconds."""
        try:
            client = await self._get_client()
            if client is None:
                return
            await client.setex(key, ttl, json.dumps(value))
        except Exception:
            logger.debug("Cache set failed for key=%s", key, exc_info=True)

    async def delete(self, key: str):
        """Delete a cached value."""
        try:
            client = await self._get_client()
            if client is None:
                return
            await client.delete(key)
        except Exception:
            logger.debug("Cache delete failed for key=%s", key, exc_info=True)

    async def cache_evaluation(self, candidate_id: str, evaluation: dict):
        """Cache evaluation results."""
        await self.set(f"eval:{candidate_id}", evaluation, ttl=7200)

    async def get_cached_evaluation(self, candidate_id: str) -> Optional[dict]:
        """Get cached evaluation results."""
        return await self.get(f"eval:{candidate_id}")

    async def cache_agent_output(self, candidate_id: str, agent_name: str, output: dict):
        """Cache individual agent output."""
        await self.set(f"agent:{candidate_id}:{agent_name}", output, ttl=3600)

    async def get_cached_agent_output(self, candidate_id: str, agent_name: str) -> Optional[dict]:
        """Get cached agent output."""
        return await self.get(f"agent:{candidate_id}:{agent_name}")


# Singleton
cache_service = CacheService()
