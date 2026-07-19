import httpx
import uuid
import asyncio
from loguru import logger
from config import API_URL

client = httpx.AsyncClient(timeout=30.0)

async def register_merchant(
    telegram_id: int,
    phone_number: str,
    business_name: str,
    business_email: str,
    telebirr_name: str,
    telebirr_number: str,
) -> dict:
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json",
    }
    payload = {
        "telegram_id": telegram_id,
        "phone_number": phone_number,
        "business_name": business_name,
        "business_email": business_email,
        "telebirr_name": telebirr_name,
        "telebirr_number": telebirr_number,
    }

    last_exception = None
    for attempt in range(3):
        try:
            response = await client.post(
                f"{API_URL}/v1/bot/register",
                json=payload,
                headers=headers,
            )
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                detail = response.json().get("detail", "Bad request")
                raise RegistrationError(detail)
            elif response.status_code >= 500:
                logger.warning(f"Server error {response.status_code} on attempt {attempt+1}")
                last_exception = httpx.HTTPStatusError(
                    f"Server error {response.status_code}",
                    request=response.request,
                    response=response,
                )
            else:
                logger.warning(f"Unexpected status {response.status_code}")
                last_exception = httpx.HTTPStatusError(
                    f"Unexpected status {response.status_code}",
                    request=response.request,
                    response=response,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning(f"Network error on attempt {attempt+1}: {exc}")
            last_exception = exc

        if attempt < 2:
            wait = 2 ** attempt
            await asyncio.sleep(wait)

    raise last_exception or RuntimeError("Registration failed")

async def get_plans() -> list[dict]:
    """Fetch active subscription plans from your backend."""
    try:
        resp = await client.get(f"{API_URL}/v1/subscriptions/plans")
        resp.raise_for_status()
        plans = resp.json()
        # Ensure each plan has at least 'id', 'name', 'price'
        return plans
    except Exception:
        logger.error("Failed to fetch plans, using fallback")
        return [
            {"id": 1, "name": "Monthly", "price": 100},
            {"id": 2, "name": "Yearly", "price": 1000},
        ]

async def subscribe(telegram_id: int, plan_id: int) -> dict:
    payload = {"telegram_id": telegram_id, "plan_id": plan_id}
    resp = await client.post(f"{API_URL}/v1/bot/subscribe", json=payload)
    if resp.status_code in (200, 201):
        return resp.json()
    detail = resp.json().get("detail", "Subscription failed")
    raise SubscriptionError(detail)

class RegistrationError(Exception):
    pass

class SubscriptionError(Exception):
    pass

async def check_merchant_status(telegram_id: int) -> bool:
    """
    Check if a merchant is already registered by Telegram ID.
    Returns True if registered, False otherwise.
    """
    try:
        # Call a backend endpoint to check registration status
        response = await client.get(
            f"{API_URL}/v1/bot/check-status/{telegram_id}"
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("is_registered", False)
        elif response.status_code == 404:
            return False
        else:
            logger.warning(f"Unexpected status {response.status_code} checking merchant status")
            return False
    except Exception as e:
        logger.error(f"Error checking merchant status: {e}")
        return False