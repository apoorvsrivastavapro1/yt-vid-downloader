from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


def ensure_download_dir() -> Path:
    settings = get_settings()
    path = Path(settings.temp_download_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def schedule_file_deletion(file_path: str, delay_seconds: int | None = None) -> None:
    """Mark file for deletion via expiry timestamp (cleanup sweep handles removal)."""
    settings = get_settings()
    delay = delay_seconds or (settings.file_expiry_minutes * 60)
    expiry_path = f"{file_path}.expires"
    expiry_time = time.time() + delay
    try:
        Path(expiry_path).write_text(str(expiry_time))
    except OSError as exc:
        logger.warning("Could not write expiry marker for %s: %s", file_path, exc)


def delete_file(path: str) -> None:
    try:
        p = Path(path)
        if p.exists():
            p.unlink()
            logger.info("Deleted file: %s", path)
        expiry = Path(f"{path}.expires")
        if expiry.exists():
            expiry.unlink()
    except OSError as exc:
        logger.error("Failed to delete %s: %s", path, exc)


def sweep_expired_files() -> int:
    """Remove files older than FILE_EXPIRY_MINUTES or past their expiry marker."""
    settings = get_settings()
    download_dir = ensure_download_dir()
    now = time.time()
    max_age = settings.file_expiry_minutes * 60
    deleted = 0

    for entry in download_dir.iterdir():
        if entry.name.endswith(".expires"):
            continue
        if not entry.is_file():
            continue

        expiry_file = download_dir / f"{entry.name}.expires"
        should_delete = False

        if expiry_file.exists():
            try:
                expiry_time = float(expiry_file.read_text().strip())
                should_delete = now >= expiry_time
            except (ValueError, OSError):
                should_delete = True
        else:
            age = now - entry.stat().st_mtime
            should_delete = age >= max_age

        if should_delete:
            delete_file(str(entry))
            deleted += 1

    if deleted:
        logger.info("Cleanup sweep removed %d file(s)", deleted)
    return deleted


def cleanup_orphan_markers() -> None:
    settings = get_settings()
    download_dir = Path(settings.temp_download_dir)
    if not download_dir.exists():
        return
    for marker in download_dir.glob("*.expires"):
        base = str(marker)[: -len(".expires")]
        if not os.path.exists(base):
            try:
                marker.unlink()
            except OSError:
                pass
