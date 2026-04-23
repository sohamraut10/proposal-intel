import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api import auth, users, jobs, proposals, analytics

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.aggregator import poll_all_platforms

    scheduler.add_job(
        poll_all_platforms,
        "interval",
        seconds=settings.JOB_POLL_INTERVAL_SECONDS,
        id="poll_platforms",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — polling every %ds", settings.JOB_POLL_INTERVAL_SECONDS)

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Proposal Intelligence API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(proposals.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.APP_ENV}
