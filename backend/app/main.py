import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import AppError
from app.middleware.cors import setup_cors
from app.middleware.rate_limiter import RateLimitMiddleware
from app.routes import download, info
from app.services import ffmpeg_service
from app.utils.file_cleanup import ensure_download_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ffmpeg_service.verify_ffmpeg()
    ensure_download_dir()   
    logger.info(
        "Started YouTube Downloader API v%s (%s)",
        settings.app_version,
        settings.app_env,
    )
    yield


app = FastAPI(
    title="YouTube Downloader API",
    version=settings.app_version,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

setup_cors(app)
app.add_middleware(RateLimitMiddleware)
app.include_router(info.router)
app.include_router(download.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "code": exc.status_code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": True, "code": 500, "message": "Internal server error"},
    )
