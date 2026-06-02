# Loop — YouTube Downloader

Monorepo for **Loop**, a minimal YouTube video & MP3 downloader. FastAPI backend + React frontend.

## Project Structure

```
YTVideoDownloader/
├── backend/                 # Python FastAPI API
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/          # /info, /download
│   │   ├── services/        # yt-dlp, ffmpeg, cache
│   │   ├── tasks/           # Celery cleanup
│   │   └── middleware/      # CORS, rate limiting
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React + Vite + Tailwind UI
│   ├── src/
│   │   ├── App.tsx          # Main page (Loop design)
│   │   ├── lib/api.ts       # API client
│   │   └── components/ui/   # Button, Input
│   ├── Dockerfile           # nginx static + /api proxy
│   └── vite.config.ts       # dev proxy → backend
├── docker-compose.yml       # redis, api, worker, beat, frontend
├── .env                     # shared env (root)
└── package.json             # convenience scripts
```

## Tech Stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3.11, FastAPI, yt-dlp, ffmpeg, Redis, Celery |
| Frontend | React 19, Vite, Tailwind CSS, lucide-react |
| Infra | Docker Compose, nginx |

## Quick Start (local dev)

### 1. Environment

```bash
cp .env.example .env
# ALLOWED_ORIGINS should include http://localhost:3000
```

### 2. Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -U yt-dlp

# Start Redis (macOS)
brew services start redis

# Terminal 1 — API
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 & 3 — Celery (optional, for file cleanup)
cd backend && celery -A app.tasks.celery_app worker --loglevel=info
cd backend && celery -A app.tasks.celery_app beat --loglevel=info
```

### 3. Frontend

```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:3000**. The Vite dev server proxies `/api/*` → `http://localhost:8000`.

Or from the repo root:

```bash
npm run dev:frontend   # frontend on :3000
npm run dev:backend    # API on :8000
```

## Docker (full stack)

```bash
cp .env.example .env
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs (dev) | http://localhost:8000/docs |

The frontend nginx container proxies `/api` to the backend, so the browser never needs direct CORS access in production.

## API Endpoints

### Health

```bash
curl http://localhost:8000/health
```

### Video Info

```bash
curl "http://localhost:8000/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Download

```bash
curl -L -o video.mp4 \
  "http://localhost:8000/download?url=...&format=mp4&quality=720p"
```

## Environment Variables

See `.env.example`. Key settings:

| Variable | Description |
|----------|-------------|
| `ALLOWED_ORIGINS` | CORS origins (include `http://localhost:3000`) |
| `REDIS_URL` | Redis for cache + rate limits |
| `VITE_API_URL` | Frontend API base (default `/api` in production) |

## Tests

```bash
cd backend && pytest -v
# or from root:
npm test
```

## License

MIT — ensure compliance with YouTube Terms of Service and applicable copyright law.
