from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_ROOT / ".env", _ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_port: int = 8000
    app_version: str = "1.0.0"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # File Storage
    temp_download_dir: str = "/tmp/downloads"
    file_expiry_minutes: int = 5

    # Rate Limiting
    rate_limit_info: int = 10
    rate_limit_info_window_seconds: int = 60
    rate_limit_download: int = 3
    rate_limit_download_window_seconds: int = 600

    # Cache
    info_cache_ttl_seconds: int = 600

    # yt-dlp
    ytdlp_cookiefile: str = ""
    ytdlp_proxy: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
