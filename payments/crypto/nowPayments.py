import httpx
from quart import jsonify
import asyncio
IPN="EeTbyKKMDjT0FxibIfGs3oB2GI/7iLsa"
API_KEY="EYCMY5K-ADD44KK-QMCMDHP-3H020C1"

async def create_invoice():
     # Replace with your actual API key
    url = "https://api.nowpayments.io/v1/invoice"

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }

    data = {
        "price_amount": 3,
        "price_currency": "usd",
        "order_id": "RGDBP-21314",
        "order_description": "PIPS MATRIX",
        "ipn_callback_url": "https://c5ff-102-88-34-245.ngrok-free.app",
        "success_url": "https://t.me/PipsMatrixfx",
        "cancel_url": "https://nowpayments.io",
        "is_fee_paid_by_user":False,
        "is_fixed_rate": True
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            result = response.json()
            return result
    except Exception as e:
        return {"error": e}
print(asyncio.run(create_invoice()))