import tempfile
from pathlib import Path
from unittest.mock import patch

VALID_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_download_mp4(client):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"fake video content")
        tmp_path = tmp.name

    try:
        with patch(
            "app.routes.download.ytdlp_service.download_video",
            return_value=(tmp_path, "video/mp4", "test-video.mp4"),
        ):
            response = client.get(
                "/download",
                params={"url": VALID_URL, "format": "mp4", "quality": "720p"},
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert b"fake video" in response.content
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_download_mp3(client):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"fake audio content")
        tmp_path = tmp.name

    try:
        with patch(
            "app.routes.download.ytdlp_service.download_video",
            return_value=(tmp_path, "audio/mpeg", "test-audio.mp3"),
        ):
            response = client.get(
                "/download",
                params={"url": VALID_URL, "format": "mp3", "quality": "128kbps"},
            )

        assert response.status_code == 200
        assert "audio/mpeg" in response.headers["content-type"]
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_download_bad_format(client):
    response = client.get(
        "/download",
        params={"url": VALID_URL, "format": "avi", "quality": "720p"},
    )
    assert response.status_code == 400
    assert response.json()["error"] is True


def test_download_invalid_url(client):
    response = client.get(
        "/download",
        params={"url": "not-a-url", "format": "mp4", "quality": "720p"},
    )
    assert response.status_code == 400


def test_download_bad_quality(client):
    from app.exceptions import InvalidURLError

    with patch(
        "app.routes.download.ytdlp_service.download_video",
        side_effect=InvalidURLError("Invalid MP4 quality. Use 360p, 720p, or 1080p."),
    ):
        response = client.get(
            "/download",
            params={"url": VALID_URL, "format": "mp4", "quality": "4k"},
        )
    assert response.status_code == 400
