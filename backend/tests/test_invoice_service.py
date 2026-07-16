import pytest
from httpx import AsyncClient
from app.main import app
from app.models.invoice import InvoiceStatus

@pytest.mark.asyncio
async def test_invoice_lifecycle_and_validation(client: AsyncClient, mock_merchant_api_key):
    """
    Validates end-to-end processing: Creation, flattened parsing constraints, 
    and public URL lookup detachment.
    """
    headers = {"X-API-Key": mock_merchant_api_key}
    payload = {
        "amount": "150.75",
        "receiver": "+251911234567",
        "callback_url": "https://my-merchant-system.com/callback",
        "expires_in_minutes": 15,
        "metadata": {
            "order_reference": "TX-9988",
            "platform": "telegram_bot"
        }
    }

    # 1. Assert Creation Works and Output Contracts map cleanly
    create_response = await client.post("/v1/invoices", json=payload, headers=headers)
    assert create_response.status_code == 201
    
    data = create_response.json()
    assert "token" in data
    assert "verification_url" in data
    assert data["status"] == InvoiceStatus.PENDING
    assert data["metadata"]["order_reference"] == "TX-9988"  # Assures model_validator structural flattening works

    generated_token = data["token"]
    invoice_id = data["id"]

    # 2. Assert Protected Namespace works via ID Lookup
    id_lookup_resp = await client.get(f"/v1/invoices/{invoice_id}", headers=headers)
    assert id_lookup_resp.status_code == 200
    assert id_lookup_resp.json()["token"] == generated_token

    # 3. Assert Public Lookup returns strictly filtered fields for Flutter Client
    public_lookup_resp = await client.get(f"/v1/invoices/token/{generated_token}")
    assert public_lookup_resp.status_code == 200
    
    public_data = public_lookup_resp.json()
    assert "id" not in public_data  # Internal primary sequence details hidden
    assert "callback_url" not in public_data  # Secure infrastructure webhooks hidden
    assert public_data["status"] == InvoiceStatus.PENDING
    assert public_data["amount"] == "150.75"