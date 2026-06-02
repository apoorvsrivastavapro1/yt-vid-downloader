import logging
import time

import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.services.cache_service import get_redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path == "/info":
            limit = get_settings().rate_limit_info
            window = get_settings().rate_limit_info_window_seconds
        elif path == "/download":
            limit = get_settings().rate_limit_download
            window = get_settings().rate_limit_download_window_seconds
        else:
            return await call_next(request)

        client_ip = _client_ip(request)
        key = f"ratelimit:{path}:{client_ip}"

        try:
            allowed, retry_after = _check_rate_limit(key, limit, window)
        except redis.RedisError as exc:
            logger.warning("Rate limit Redis error, allowing request: %s", exc)
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "code": 429,
                    "message": "Too many requests, slow down",
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    r = get_redis()
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds + 1)
    results = pipe.execute()
    count = results[2]
    if count > limit:
        oldest = r.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = int(window_seconds - (now - oldest[0][1])) + 1
        else:
            retry_after = window_seconds
        return False, max(retry_after, 1)
    return True, 0
