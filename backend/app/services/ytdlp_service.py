import logging
import re
import uuid
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

from app.config import get_settings
from app.exceptions import (
    AgeRestrictedError,
    ExtractionError,
    InvalidURLError,
    VideoNotAvailableError,
)
from app.services import ffmpeg_service
from app.utils.file_cleanup import ensure_download_dir, schedule_file_deletion
from app.utils.validators import is_youtube_url, normalize_youtube_url

logger = logging.getLogger(__name__)

MP3_QUALITIES = [
    {"quality": "128kbps", "format_id": "mp3_128"},
    {"quality": "320kbps", "format_id": "mp3_320"},
]

MP4_QUALITIES = [
    {"quality": "360p", "format_id": "18"},
    {"quality": "720p", "format_id": "22"},
    {"quality": "1080p", "format_id": "137+140"},
]

MP4_FORMAT_SELECTORS = {
    "360p": "18/best[height<=360][ext=mp4]/best[height<=360]",
    "720p": "22/best[height<=720][ext=mp4]/best[height<=720]",
    "1080p": "137+140/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
}

MP3_FORMAT_SELECTORS = {
    "128kbps": "bestaudio/best",
    "320kbps": "bestaudio/best",
}


def _base_opts() -> dict[str, Any]:
    settings = get_settings()
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": False,
    }
    if settings.ytdlp_cookiefile:
        opts["cookiefile"] = settings.ytdlp_cookiefile
    if settings.ytdlp_proxy:
        opts["proxy"] = settings.ytdlp_proxy
    return opts


def _map_ytdlp_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if "private" in msg or "unavailable" in msg or "removed" in msg or "deleted" in msg:
        raise VideoNotAvailableError() from exc
    if "age" in msg or "sign in" in msg or "confirm your age" in msg:
        raise AgeRestrictedError() from exc
    if "invalid" in msg or "unsupported url" in msg:
        raise InvalidURLError() from exc
    raise ExtractionError() from exc


def get_info(url: str) -> dict[str, Any]:
    if not is_youtube_url(url):
        raise InvalidURLError()

    normalized = normalize_youtube_url(url)
    opts = _base_opts()
    opts.update(
        {
            "skip_download": True,
            "extract_flat": False,
        }
    )

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(normalized, download=False)
    except (DownloadError, ExtractorError) as exc:
        logger.exception("yt-dlp info extraction failed for %s", normalized)
        _map_ytdlp_error(exc)

    if not info:
        raise VideoNotAvailableError()

    duration = info.get("duration") or 0
    upload_date = info.get("upload_date")
    formatted_upload = None
    if upload_date and len(upload_date) == 8:
        formatted_upload = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

    return {
        "title": info.get("title") or "Unknown",
        "thumbnail": info.get("thumbnail") or "",
        "duration": duration,
        "duration_formatted": _format_duration(duration),
        "channel": info.get("channel") or info.get("uploader") or "",
        "view_count": info.get("view_count") or 0,
        "upload_date": formatted_upload,
        "formats": {
            "mp3": MP3_QUALITIES,
            "mp4": MP4_QUALITIES,
        },
    }


def download_video(url: str, fmt: str, quality: str) -> tuple[str, str, str]:
    """
    Download and process media. Returns (file_path, content_type, safe_filename).
    """
    if not is_youtube_url(url):
        raise InvalidURLError()

    normalized = normalize_youtube_url(url)
    fmt = fmt.lower().strip()
    if fmt not in ("mp3", "mp4"):
        raise InvalidURLError("Invalid format. Use mp3 or mp4.")

    if fmt == "mp3" and quality not in MP3_FORMAT_SELECTORS:
        raise InvalidURLError("Invalid MP3 quality. Use 128kbps or 320kbps.")
    if fmt == "mp4" and quality not in MP4_FORMAT_SELECTORS:
        raise InvalidURLError("Invalid MP4 quality. Use 360p, 720p, or 1080p.")

    download_dir = ensure_download_dir()
    job_id = uuid.uuid4().hex
    outtmpl = str(download_dir / f"{job_id}.%(ext)s")

    info_opts = _base_opts()
    info_opts["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            meta = ydl.extract_info(normalized, download=False)
    except (DownloadError, ExtractorError) as exc:
        _map_ytdlp_error(exc)

    title = meta.get("title") or "download"
    safe_name = _sanitize_filename(title)

    if fmt == "mp3":
        return _download_mp3(normalized, quality, job_id, download_dir, safe_name)
    return _download_mp4(normalized, quality, job_id, download_dir, safe_name, meta)


def _download_mp3(
    url: str,
    quality: str,
    job_id: str,
    download_dir: Path,
    safe_name: str,
) -> tuple[str, str, str]:
    raw_path = download_dir / f"{job_id}_raw"
    final_path = download_dir / f"{job_id}.mp3"

    opts = _base_opts()
    opts.update(
        {
            "format": MP3_FORMAT_SELECTORS[quality],
            "outtmpl": str(raw_path) + ".%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }
            ],
        }
    )

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except (DownloadError, ExtractorError) as exc:
        logger.exception("MP3 download failed")
        _map_ytdlp_error(exc)

    raw_files = list(download_dir.glob(f"{job_id}_raw*"))
    if not raw_files:
        raise ExtractionError("Audio download produced no file")

    source = str(raw_files[0])
    ffmpeg_service.convert_to_mp3(source, str(final_path), quality)
    for f in raw_files:
        ffmpeg_service.safe_remove(f)

    schedule_file_deletion(str(final_path))
    return str(final_path), "audio/mpeg", f"{safe_name}.mp3"


def _download_mp4(
    url: str,
    quality: str,
    job_id: str,
    download_dir: Path,
    safe_name: str,
    meta: dict,
) -> tuple[str, str, str]:
    final_path = download_dir / f"{job_id}.mp4"
    selector = MP4_FORMAT_SELECTORS[quality]

    opts = _base_opts()
    opts.update(
        {
            "format": selector,
            "outtmpl": str(download_dir / f"{job_id}.%(ext)s"),
            "merge_output_format": "mp4",
        }
    )

    if "+" in selector:
        opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except (DownloadError, ExtractorError) as exc:
        logger.exception("MP4 download failed")
        _map_ytdlp_error(exc)

    candidates = list(download_dir.glob(f"{job_id}*"))
    media_files = [p for p in candidates if p.suffix.lower() in (".mp4", ".mkv", ".webm")]

    if not media_files:
        raise ExtractionError("Video download produced no file")

    source = media_files[0]
    if source.suffix.lower() != ".mp4" or source != final_path:
        if len(media_files) >= 2:
            video = next((p for p in media_files if "video" in p.name or p.suffix == ".mp4"), media_files[0])
            audio = next((p for p in media_files if p != video), None)
            if audio:
                ffmpeg_service.merge_to_mp4(str(video), str(audio), str(final_path))
                ffmpeg_service.safe_remove(video)
                ffmpeg_service.safe_remove(audio)
            else:
                ffmpeg_service.remux_single_file(str(source), str(final_path))
                ffmpeg_service.safe_remove(source)
        elif source != final_path:
            ffmpeg_service.remux_single_file(str(source), str(final_path))
            ffmpeg_service.safe_remove(source)
    elif source != final_path:
        source.rename(final_path)

    schedule_file_deletion(str(final_path))
    return str(final_path), "video/mp4", f"{safe_name}.mp4"


def _format_duration(seconds: int) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return (name[:200] or "download").strip(". ")
