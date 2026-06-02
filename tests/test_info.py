from unittest.mock import patch

import pytest

SAMPLE_INFO = {
    "title": "Test Video",
    "thumbnail": "https://img.youtube.com/vi/abc123/hqdefault.jpg",
    "duration": 272,
    "duration_formatted": "4:32",
    "channel": "Test Channel",
    "view_count": 1000000,
    "upload_date": "2024-01-15",
    "formats": {
        "mp3": [
            {"quality": "128kbps", "format_id": "mp3_128"},
            {"quality": "320kbps", "format_id": "mp3_320"},
        ],
        "mp4": [
            {"quality": "360p", "format_id": "18"},
            {"quality": "720p", "format_id": "22"},
            {"quality": "1080p", "format_id": "137+140"},
        ],
    },
}

VALID_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_info_valid_url(client):
    with patch("app.routes.info.ytdlp_service.get_info", return_value=SAMPLE_INFO):
        response = client.get("/info", params={"url": VALID_URL})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Video"
    assert "formats" in data
    assert "mp3" in data["formats"]
    assert "mp4" in data["formats"]


def test_info_invalid_url(client):
    response = client.get("/info", params={"url": "https://example.com/not-youtube"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] is True
    assert body["code"] == 400


def test_info_playlist_rejected(client):
    response = client.get(
        "/info",
        params={"url": "https://www.youtube.com/watch?v=abc&list=PLxyz"},
    )
    assert response.status_code == 400


def test_info_private_video(client):
    from app.exceptions import VideoNotAvailableError

    with patch(
        "app.routes.info.ytdlp_service.get_info",
        side_effect=VideoNotAvailableError(),
    ):
        response = client.get("/info", params={"url": VALID_URL})

    assert response.status_code == 404
    assert response.json()["message"] == "Video not available"


def test_info_age_restricted(client):
    from app.exceptions import AgeRestrictedError

    with patch(
        "app.routes.info.ytdlp_service.get_info",
        side_effect=AgeRestrictedError(),
    ):
        response = client.get("/info", params={"url": VALID_URL})

    assert response.status_code == 403
