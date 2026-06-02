# YouTube Downloader Backend

Production-ready FastAPI backend that accepts YouTube URLs, returns video metadata, and streams downloaded MP3/MP4 files. Designed to be consumed by a separate Next.js frontend.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- yt-dlp (YouTube extraction)
- ffmpeg (audio/video processing)
- Redis (caching + rate limiting)
- Celery (background file cleanup)
- Docker + Docker Compose

## Prerequisites

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) installed and on `PATH`
- Redis 7+ (local or via Docker)

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Environment settings
├── routes/
│   ├── info.py          # GET /info
│   └── download.py      # GET /download
├── services/
│   ├── ytdlp_service.py # yt-dlp metadata & downloads
│   ├── ffmpeg_service.py
│   └── cache_service.py # Redis metadata cache
├── tasks/
│   └── download_task.py # Celery cleanup sweep
├── middleware/
│   ├── rate_limiter.py  # IP rate limits (Redis)
│   └── cors.py
└── utils/
    ├── validators.py
    └── file_cleanup.py
tests/
Dockerfile
docker-compose.yml
```

## API Endpoints

### Health

```bash
curl http://localhost:8000/health
```

```json
{ "status": "ok", "version": "1.0.0" }
```

### Video Info

```bash
curl "http://localhost:8000/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Returns title, thumbnail, duration, channel, view count, and format options for MP3/MP4.

### Download

```bash
# MP4 720p
curl -L -o video.mp4 \
  "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&format=mp4&quality=720p"

# MP3 320kbps
curl -L -o audio.mp3 \
  "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&format=mp3&quality=320kbps"
```

Streams the file with `Content-Disposition: attachment`.

### Error Responses

All errors return JSON:

```json
{ "error": true, "code": 404, "message": "Video not available" }
```

| Scenario            | Code |
|---------------------|------|
| Invalid URL         | 400  |
| Age-restricted      | 403  |
| Private/deleted     | 404  |
| Rate limit          | 429  |
| yt-dlp failure      | 502  |
| Server error        | 500  |

## Environment Variables

Copy `.env.example` to `.env` and adjust:

| Variable | Description |
|----------|-------------|
| `APP_ENV` | `development` or `production` |
| `APP_PORT` | API port (default 8000) |
| `APP_VERSION` | Shown in `/health` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `REDIS_URL` | Redis connection URL |
| `TEMP_DOWNLOAD_DIR` | Temp storage (default `/tmp/downloads`) |
| `FILE_EXPIRY_MINUTES` | Auto-delete files after N minutes |
| `RATE_LIMIT_INFO` | Max `/info` requests per IP per window |
| `RATE_LIMIT_INFO_WINDOW_SECONDS` | Window for info limit (default 60) |
| `RATE_LIMIT_DOWNLOAD` | Max `/download` requests per IP per window |
| `RATE_LIMIT_DOWNLOAD_WINDOW_SECONDS` | Window for download limit (default 600) |
| `INFO_CACHE_TTL_SECONDS` | Metadata cache TTL (default 600) |
| `YTDLP_COOKIEFILE` | Optional cookies.txt path |
| `YTDLP_PROXY` | Optional proxy URL |

## Local Setup (without Docker)

```bash
# Clone and enter project
cd YTVideoDownloader

# Create virtualenv
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -U yt-dlp

# Configure environment
cp .env.example .env

# Start Redis (macOS with Homebrew)
brew services start redis

# Create download directory
mkdir -p /tmp/downloads

# Run API
uvicorn app.main:app --reload --port 8000

# In separate terminals — Celery worker + beat for cleanup
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

API docs (development only): http://localhost:8000/docs

## Docker Setup

```bash
cp .env.example .env
# Edit .env — ALLOWED_ORIGINS, etc.

docker compose up -d --build
```

Services:

| Service | Role |
|---------|------|
| `api` | FastAPI on port 8000 |
| `redis` | Cache + rate limits + Celery broker |
| `worker` | Celery worker |
| `beat` | Cleanup sweep every 5 minutes |

```bash
docker compose logs -f api
curl http://localhost:8000/health
```

## Running Tests

```bash
pip install -r requirements.txt
pytest -v
```

Tests mock yt-dlp and Redis so no live YouTube calls are required.

## Deployment (Ubuntu VPS)

Example flow for DigitalOcean / Hetzner:

### 1. Install Docker

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

### 2. Clone and configure

```bash
git clone <your-repo-url> youtube-downloader
cd youtube-downloader
cp .env.example .env
nano .env   # Set APP_ENV=production, ALLOWED_ORIGINS=https://yourdomain.com
```

### 3. Start services

```bash
docker compose up -d --build
```

### 4. Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;
        client_max_body_size 10M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/youtube-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5. TLS (recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### 6. DNS

Point `api.yourdomain.com` A record to your VPS IP.

## Security Notes

- Files are stored only in `/tmp/downloads` with UUID names and deleted after serving or expiry.
- Internal paths are never returned in API responses.
- Rate limiting is enforced per IP via Redis.
- Set `ALLOWED_ORIGINS` to your frontend domain only in production.

## License

MIT — ensure compliance with YouTube Terms of Service and applicable copyright law in your jurisdiction.
