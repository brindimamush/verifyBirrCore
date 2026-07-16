import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.callback import CallbackJob, CallbackAttempt, CallbackStatus
from app.core.callbacks import prepare_signed_headers
import structlog

logger = structlog.get_logger()
MAX_RETRIES = 5

async def execute_callback(db: AsyncSession, job: CallbackJob):
    job.attempt_count += 1
    headers = prepare_signed_headers(job.payload)
    
    attempt = CallbackAttempt(job_id=job.id, attempt_number=job.attempt_count)
    db.add(attempt)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(job.url, json=job.payload, headers=headers)
            
            attempt.status_code = response.status_code
            attempt.response_body = response.text[:500] # Truncate massive responses
            
            if 200 <= response.status_code < 300:
                job.status = CallbackStatus.SUCCESS
                logger.info("callback_delivered", job_id=job.id, url=job.url)
            else:
                handle_retry(job, attempt, f"HTTP Error {response.status_code}")
                
    except httpx.RequestError as e:
        attempt.error_message = str(e)
        handle_retry(job, attempt, f"Network Error: {str(e)}")
        
    await db.commit()

def handle_retry(job: CallbackJob, attempt: CallbackAttempt, reason: str):
    logger.warning("callback_failed", job_id=job.id, attempt=job.attempt_count, reason=reason)
    
    if job.attempt_count >= MAX_RETRIES:
        job.status = CallbackStatus.EXHAUSTED
        logger.error("callback_exhausted", job_id=job.id)
    else:
        # Exponential backoff: 15s, 30s, 60s, 120s...
        backoff_seconds = (2 ** job.attempt_count) * 15
        job.next_attempt_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=backoff_seconds)

async def run_worker():
    """Main worker loop to poll for pending callbacks."""
    logger.info("Starting Callback Engine Worker...")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(CallbackJob).where(
                    CallbackJob.status == CallbackStatus.PENDING,
                    CallbackJob.next_attempt_at <= datetime.now(timezone.utc).replace(tzinfo=None)
                ).order_by(CallbackJob.next_attempt_at.asc()).limit(50)
                
                result = await db.execute(stmt)
                jobs = result.scalars().all()
                
                if jobs:
                    tasks = [execute_callback(db, job) for job in jobs]
                    await asyncio.gather(*tasks)
                else:
                    await asyncio.sleep(5) # Pause if queue is empty
        except Exception as e:
            logger.error("worker_crash_recovered", error=str(e))
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_worker())