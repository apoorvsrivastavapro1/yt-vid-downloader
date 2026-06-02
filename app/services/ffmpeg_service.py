from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from app.exceptions import ExtractionError

logger = logging.getLogger(__name__)

MP3_BITRATES = {"128kbps": "128k", "320kbps": "320k"}


def verify_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError(
            "ffmpeg is not installed or not on PATH. Install ffmpeg before starting the server."
        )
    return path


def convert_to_mp3(input_path: str, output_path: str, quality: str) -> str:
    bitrate = MP3_BITRATES.get(quality, "192k")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        bitrate,
        output_path,
    ]
    _run_ffmpeg(cmd, "MP3 conversion failed")
    return output_path


def merge_to_mp4(video_path: str, audio_path: str, output_path: str) -> str:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-strict",
        "experimental",
        output_path,
    ]
    _run_ffmpeg(cmd, "MP4 merge failed")
    return output_path


def remux_single_file(input_path: str, output_path: str) -> str:
    """Copy streams into a clean MP4 container."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c",
        "copy",
        output_path,
    ]
    _run_ffmpeg(cmd, "MP4 remux failed")
    return output_path


def _run_ffmpeg(cmd: list[str], error_message: str) -> None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if result.returncode != 0:
            logger.error("ffmpeg stderr: %s", result.stderr[-2000:])
            raise ExtractionError(error_message)
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError("ffmpeg processing timed out") from exc
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found") from exc


def safe_remove(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Could not remove %s: %s", path, exc)
