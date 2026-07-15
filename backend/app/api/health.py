from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
from app.db.session import get_db
from app.db.redis import get_redis
import structlog

router = APIRouter()
logger = structlog.get_logger()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    try:
        await db.execute(text("SELECT 1"))
        await redis_client.ping()
        logger.info("Readiness check passed")
        return {"status": "ready", "database": "connected", "redis": "connected"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")