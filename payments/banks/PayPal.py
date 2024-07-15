import base64

import httpx
API_KEY=""
CLIENT_ID=''
client_credentials = f"{CLIENT_ID}:{API_KEY}"
encoded_credentials=base64.b64encode(client_credentials.encode()).decode()
async def create_paypal_order():
    url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

    headers = {
        'Content-Type': 'application/json',
        'PayPal-Request-Id': 'ra',
        'Authorization': f"Basic {encoded_credentials}"
    }

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": "drr",
                "amount": {
                    "currency_code": "USD",
                    "value": "100.00"
                },
                "shipping": {
                    "address": {
                        "address_line_1": "123 Main St",
                        "address_line_2": "Apt 4",
                        "admin_area_2": "San Jose",
                        "admin_area_1": "CA",
                        "postal_code": "95131",
                        "country_code": "US"
                    }
                }
            }
        ],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "brand_name": "EXAMPLE INC",
                    "locale": "en-US",
                    "landing_page": "LOGIN",
                    "shipping_preference": "SET_PROVIDED_ADDRESS",
                    "user_action": "PAY_NOW",
                    "return_url": "https://example.com/returnUrl",
                    "cancel_url": "https://example.com/cancelUrl"
                }
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            result = response.json()
            return result
    except Exception as e:
        return (f"Exception occured :{e}")

# Example usage
async def main():
    try:
        result = await create_paypal_order()
        print(result)
    except Exception as e:
        print(e)

# Run the example
import asyncio
asyncio.run(main())
