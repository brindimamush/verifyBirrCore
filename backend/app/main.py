from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.merchants import router as merchants_router
from app.api.api_keys import router as api_keys_router

import structlog

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

app = FastAPI(title="Payment Verification Platform")

app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(merchants_router, tags=["Merchants"])
app.include_router(api_keys_router, tags=["API Keys"])