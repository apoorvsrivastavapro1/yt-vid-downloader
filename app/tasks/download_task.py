import logging

from app.tasks.celery_app import celery_app
from app.utils.file_cleanup import cleanup_orphan_markers, sweep_expired_files

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.download_task.cleanup_expired_files")
def cleanup_expired_files() -> dict:
    deleted = sweep_expired_files()
    cleanup_orphan_markers()
    logger.info("Scheduled cleanup completed, deleted=%d", deleted)
    return {"deleted": deleted}
