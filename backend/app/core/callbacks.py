import hmac
import hashlib
import time
import secrets
import json
from app.core.config import settings

def generate_signature(payload: dict, timestamp: str, nonce: str) -> str:
    """Generates an HMAC SHA-256 signature for the callback payload."""
    # Note: In a multi-tenant system, this should ideally use a merchant-specific Webhook Secret.
    # We are using the application SECRET_KEY here as the shared key foundation.
    secret = settings.SECRET_KEY.encode('utf-8')
    
    # Minimize JSON payload to ensure consistent hashing
    serialized_payload = json.dumps(payload, separators=(',', ':'))
    message = f"{timestamp}.{nonce}.{serialized_payload}"
    
    return hmac.new(secret, message.encode('utf-8'), hashlib.sha256).hexdigest()

def prepare_signed_headers(payload: dict) -> dict:
    """Prepares the security headers required for merchant callback verification."""
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    signature = generate_signature(payload, timestamp, nonce)
    
    return {
        "Content-Type": "application/json",
        "X-Verification-Timestamp": timestamp,
        "X-Verification-Nonce": nonce,
        "X-Verification-Signature": signature
    }