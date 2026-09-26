"""Demo FastAPI application for ReleaseShield demo repository."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.payments import router as payments_router

app = FastAPI(
    title="Payment Service",
    description="Demo payment processing service for ReleaseShield",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "payment-service"}
