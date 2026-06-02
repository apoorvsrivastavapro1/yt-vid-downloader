from __future__ import annotations

import json
import logging
from typing import Any

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def cache_key(prefix: str, url: str) -> str:
    from app.utils.validators import normalize_youtube_url

    return f"{prefix}:{normalize_youtube_url(url)}"


def get_cached_info(url: str) -> dict[str, Any] | None:
    try:
        raw = get_redis().get(cache_key("info", url))
        if raw:
            return json.loads(raw)
    except (redis.RedisError, json.JSONDecodeError) as exc:
        logger.warning("Redis cache read failed: %s", exc)
    return None


def set_cached_info(url: str, data: dict[str, Any]) -> None:
    settings = get_settings()
    try:
        get_redis().setex(
            cache_key("info", url),
            settings.info_cache_ttl_seconds,
            json.dumps(data),
        )
    except redis.RedisError as exc:
        logger.warning("Redis cache write failed: %s", exc)
