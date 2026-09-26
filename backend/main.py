"""
ReleaseShield - AI-powered Change Impact & Release Readiness Engine
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .routers import analyze, impact, remediate, verify, report, events, demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("releaseshield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ReleaseShield starting up")
    logger.info(f"Demo repo: {settings.DEMO_REPO_PATH}")
    logger.info(f"Bob path: {settings.BOB_EXECUTABLE}")
    yield
    logger.info("ReleaseShield shutting down")


app = FastAPI(
    title="ReleaseShield API",
    description="AI-powered Change Impact & Release Readiness Engine",
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

app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(impact.router, prefix="/api", tags=["impact"])
app.include_router(remediate.router, prefix="/api", tags=["remediate"])
app.include_router(verify.router, prefix="/api", tags=["verify"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(demo.router, prefix="/api", tags=["demo"])


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "releaseshield",
        "version": "1.0.0",
        "demo_repo": settings.DEMO_REPO_PATH,
    }
