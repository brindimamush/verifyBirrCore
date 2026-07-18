from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.merchants import router as merchants_router
from app.api.api_keys import router as api_keys_router
from app.api.invoices import router as invoices_router
from app.api.verification import router as verification_router
from app.api.subscriptions import router as subscriptions_router
from app.api.admin import router as admin_router
from app.api.bot import router as bot_router

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
app.include_router(invoices_router, tags=["Invoice Service"])
app.include_router(verification_router, tags=["Verification"])
app.include_router(subscriptions_router, tags=["Subscriptions"])
app.include_router(admin_router, tags=["Admin Dashboard"])
app.include_router(bot_router, tags=["Telegram Bot Integration"])