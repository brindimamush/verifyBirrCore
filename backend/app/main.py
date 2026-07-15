from fastapi import FastAPI
from app.api.health import router as health_router
import structlog

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

app = FastAPI(title="Payment Verification Platform")

app.include_router(health_router, tags=["Health"])