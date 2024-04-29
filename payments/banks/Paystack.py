import asyncio
import hashlib
import hmac
import os
from urllib.parse import urlparse, parse_qs
from bot.userManagment import add_user_to_group,add_transaction,convert_country_code
from quart import jsonify, request
import httpx  # Async HTTP client
from config.quartServer import app
from config.config_management import config_manager

# Get metadata and paystack_config constants
METADATA = config_manager().get_metadata_config()
PAYSTACK_CONFIG = config_manager().get_paystack_config()

async def create_paystack_checkout(telegramId,firstName,email,price,duration):
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {PAYSTACK_CONFIG["paystack_apikey"]}',
        'Content-Type': 'application/json',
    }
    payload = {
        'key': PAYSTACK_CONFIG["paystack_publickey"],
        'email': email,
        'amount': int(price) * 1400 * 100,  # Amount should be in kobo (the smallest unit of currency in Nigeria)
        'currency': 'NGN',
        'channels': ['card', 'bank', 'ussd', 'qr', 'mobile_money', 'bank_transfer'],
        'metadata':  {'telegramId':telegramId,"duration":duration,"firstName":firstName},
        'callback_url': METADATA['success_url']
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response_data = response.json()
            if response.status_code==200:
                authorization_url = response_data['data']['authorization_url']
                return authorization_url
            else:
                return False
        except httpx.HTTPError as e:
            print(f"An error occurred: {e}")

def verify_paystack_webhook(payload, secret_key, signature):
    generated_signature = hmac.new(
        secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    # Compare the generated signature with the one sent with the webhook
    return generated_signature == signature

def is_paystack_webhook(headers):
    return 'X-Paystack-Signature' in headers

@app.route('/')
def test():
    return {"message": "Your bot is up and running"}

@app.route('/paystack', methods=['POST'])
async def paystackWebhook():
    try:
        json_data = await request.get_json()
        event_data = json_data.get("data", {})
        signature = request.headers.get('X-Paystack-Signature')

        if not is_paystack_webhook(request.headers) or not verify_paystack_webhook(await request.get_data(), PAYSTACK_CONFIG["paystack_apikey"], signature):
            return jsonify({"message": "Bad Request"}), 400

        reference = event_data.get('reference')
        verify_url = f'https://api.paystack.co/transaction/verify/{reference}'
        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url, headers={'Authorization': f'Bearer {PAYSTACK_CONFIG["paystack_apikey"]}'})

        if response.status_code != 200:
            return jsonify({"message": "Verification failed"}), 400

        response_data = response.json()
        
        payment_status = event_data.get("status")

        if payment_status == 'success':
            # Accessing the id, status, and metadata id
            
            transaction_id = event_data.get("id")
            amount=event_data.get("amount")/100
            firstName = event_data.get("metadata", {}).get("firstName")
            telegramId = event_data.get("metadata", {}).get("telegramId")
            duration = event_data.get("metadata", {}).get("duration")
            country = event_data.get("authorization", {}).get("country_code")

            await add_user_to_group(user_id=telegramId,first_name=firstName,duration=duration)
            await add_transaction(transaction_id,"SUCCESS",str(amount),"Naira","Paystack",duration,telegramId,convert_country_code(country))
            return jsonify({"message": "Verification Succes"}), 200


    except Exception as e:
        print(e) 
        return jsonify({"error": "Internal server Error"}), 500
