import hashlib
import hmac
import os
import re
import uuid
import httpx
from quart import request, jsonify, Quart
from bot.userManagment import add_user_to_group,add_transaction
from config.quartServer import app
from config.config_management import config_manager

metadata=config_manager().get_metadata_config()

# Your NowPayments API key
API_KEY=config_manager().get_nowpayment_config()['nowpayment_apikey']
IPN_SECRET=config_manager().get_nowpayment_config()['nowpayment_ipnsecret']

def random_alphanumeric_string():
    random_uuid = str(uuid.uuid4()).replace("-", "")[:6]
    return random_uuid

async def create_nowpayment_invoice(chat_id,duration,amount):
    url = "https://api-sandbox.nowpayments.io/v1/invoice"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "price_amount": amount,
        "price_currency": "usd",
        "order_id": f"id{chat_id}nowPay{random_alphanumeric_string()}dur{duration}",
        "order_description": metadata['description'],
        "ipn_callback_url": f"{os.getenv('domain')}/nowpayments",
        "success_url": metadata['success_url'],
        "is_fee_paid_by_user": True,
        "is_fixed_rate": True
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            result = response.json()
            return result['invoice_url']
    except Exception as e:
        return {"error": str(e)}

async def verify_nowpayments_webhook(received_hmac,request_data):

    received_hmac = request.headers.get('x-nowpayments-sig')
    hmac_object = hmac.new(IPN_SECRET.encode('utf-8'), request_data.encode('utf-8'), hashlib.sha512)
    calculated_hmac=hmac_object.hexdigest()
    if calculated_hmac == received_hmac:
        return True
    else:
        return False
processedPayments=set()
@app.route('/nowpayments', methods=['POST'])
async def nowpayments_webhook():
    try:
        signature = request.headers.get('X-Nowpayments-Sig')
        data_text = await request.get_data(as_text=True)
        if not await verify_nowpayments_webhook(signature, data_text):
            return jsonify({"message": "Verification failed"}), 400
        
        data=await request.get_json()
        status=data['payment_status']
        if (status=='finished'):      
            transaction_id = data["payment_id"]
            if transaction_id in processedPayments:
                return jsonify({"message": "Payment already processed"}), 200
            amount = data["price_amount"]
            order_id=data['order_id']
            currency="USD"
            chatid_match = re.search(r'id(\d+)', order_id)
            telegram_id= chatid_match.group(1)
            dur_number_match = re.search(r'dur(\d+)',order_id)
            duration = dur_number_match.group(1)
            processedPayments.add(transaction_id)
            await add_transaction(transaction_id, 'SUCCESS', amount, currency, 'NowPayments', duration, telegram_id, "Unknown")
            await add_user_to_group(user_id=telegram_id, duration=duration)
            return jsonify({"message": "Verification success"}), 200
        else:
            return jsonify({"message": "Status not complete"}), 400
    except :
        return jsonify({"message": "Internal server error"}), 500

