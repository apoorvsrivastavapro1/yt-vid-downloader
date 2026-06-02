import asyncio
import logging

from fastapi import APIRouter, Query

from app.exceptions import AppError
from app.services import cache_service, ytdlp_service
from app.utils.validators import is_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["info"])


@router.get("/info")
async def video_info(url: str = Query(..., description="YouTube video URL")):
    if not is_youtube_url(url):
        from app.exceptions import InvalidURLError

        raise InvalidURLError()

    cached = cache_service.get_cached_info(url)
    if cached:
        logger.info("Cache hit for info: %s", url[:80])
        return cached

    try:
        data = await asyncio.to_thread(ytdlp_service.get_info, url)
        cache_service.set_cached_info(url, data)
        return data
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /info")
        raise AppError("Internal server error", 500) from exc
