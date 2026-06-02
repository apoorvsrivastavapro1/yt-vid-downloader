from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "youtube_downloader",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.download_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-files": {
            "task": "app.tasks.download_task.cleanup_expired_files",
            "schedule": crontab(minute="*/5"),
        },
    },
)
