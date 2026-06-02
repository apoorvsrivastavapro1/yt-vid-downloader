import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")


@pytest.fixture
def mock_redis():
    store: dict = {}

    class FakeRedis:
        def pipeline(self):
            return self

        def zremrangebyscore(self, key, min_score, max_score):
            return self

        def zadd(self, key, mapping):
            return self

        def zcard(self, key):
            return 0

        def expire(self, key, ttl):
            return self

        def execute(self):
            return [0, True, 0, True]

        def zrange(self, key, start, end, withscores=False):
            return []

        def get(self, key):
            return store.get(key)

        def setex(self, key, ttl, value):
            store[key] = value

    fake = FakeRedis()
    with patch("app.services.cache_service.get_redis", return_value=fake):
        with patch("app.middleware.rate_limiter.get_redis", return_value=fake):
            yield fake


@pytest.fixture
def client(mock_redis):
    with patch("app.services.ffmpeg_service.verify_ffmpeg", return_value="/usr/bin/ffmpeg"):
        from app.main import app

        with TestClient(app) as c:
            yield c
