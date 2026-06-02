import asyncio
import logging
import os
from typing import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.exceptions import AppError, InvalidURLError
from app.services import ytdlp_service
from app.utils.file_cleanup import delete_file
from app.utils.validators import is_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["download"])

CHUNK_SIZE = 1024 * 256


@router.get("/download")
async def download(
    url: str = Query(..., description="YouTube video URL"),
    format: str = Query(..., alias="format", description="mp3 or mp4"),
    quality: str = Query(..., description="Quality preset"),
):
    if not is_youtube_url(url):
        raise InvalidURLError()

    fmt = format.lower().strip()
    if fmt not in ("mp3", "mp4"):
        raise InvalidURLError("Invalid format. Use mp3 or mp4.")

    try:
        file_path, content_type, filename = await asyncio.to_thread(
            ytdlp_service.download_video, url, fmt, quality
        )
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /download")
        raise AppError("Internal server error", 500) from exc

    if not os.path.isfile(file_path):
        raise AppError("Download failed", 500)

    logger.info("Streaming download: %s (%s)", filename, content_type)

    return StreamingResponse(
        _file_iterator(file_path),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


async def _file_iterator(path: str) -> AsyncIterator[bytes]:
    try:
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk
    finally:
        delete_file(path)
