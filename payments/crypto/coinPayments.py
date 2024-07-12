import hashlib
import hmac
import json
import os
from urllib.parse import parse_qs, urlencode
import requests
from bot.userManagment import add_user_to_group,add_transaction
from config.config_management import config_manager
# Replace these values with your actual CoinPayments API keys
PUBLIC_KEY = config_manager().get_coinpayment_config()['coinpayment_publickey']
PRIVATE_KEY = config_manager().get_coinpayment_config()['coinpayment_apikey']
MERCHANT_ID =config_manager().get_coinpayment_config()['coinpayment_merchantId']
IPN_SECRET = config_manager().get_coinpayment_config()['coinpayment_ipnsecret']
metadata=config_manager().get_metadata_config()

from config.quartServer import app
from quart import  jsonify, request


def generate_hmac(data, secret_key):
    hmac_object = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha512)
    return hmac_object.hexdigest()

def verify_coinpayments_webhook(signature, data, merchant_id):
    calculated_hmac = generate_hmac(data, IPN_SECRET)
    return signature == calculated_hmac and merchant_id == MERCHANT_ID

def create_coinpayment_transaction(telegramId,duration,amount,email):

    main_fields = {
        'version': '1',
        'key': PUBLIC_KEY,
        'cmd': 'create_transaction',

    'amount': amount,
    'currency1': 'USD',
    'currency2': 'LTCT',
    'buyer_email':email,#passed by code
    'item_name': metadata['name'],
    'ipn_url': f"{os.getenv('domain')}/coinpayments",
    'success_url': metadata['success_url'],
    'custom':f'telegramId:{telegramId},duration:{duration}'
}

    raw_data =urlencode(main_fields)
    hmac_signature = generate_hmac(raw_data, PRIVATE_KEY)

    headers = {'HMAC': hmac_signature}
    COINPAYMENTS_API_URL = 'https://www.coinpayments.net/api.php'
    response = requests.post(COINPAYMENTS_API_URL, data=main_fields, headers=headers)

    if response.ok:
        data = response.json()
        result = data['result']
        amount=result["amount"]
        address = result['address']
        transaction_status = result['status_url']
        qr_code = result['qrcode_url']

        returndata = {'amount':amount,'address': address, "transaction_status": transaction_status, "qr_code": qr_code}
        return returndata

    else:
        print(f"Error: {response.status_code}, {response.text}")
processedPayments=set()
@app.route('/coinpayments', methods=['POST'])
async def coinpaymentwebhook():
    try:
        signature = request.headers.get('Hmac')
        data_text = await request.get_data(as_text=True)

        data = await request.data
        decoded_string = data.decode('utf-8')
        url_data = parse_qs(decoded_string)
        parsed_data = {key: value[0] if len(value) == 1 else value for key, value in url_data.items()}
        merchant_id = parsed_data.get('merchant')
        transaction_id = parsed_data.get('txn_id')

        if not verify_coinpayments_webhook(signature, data_text, merchant_id):
            return jsonify({"message": "Verification failed"}), 400

        if transaction_id in processedPayments:
            return jsonify({"message": "Payment already processed"}), 200

        status = parsed_data.get('status')
        if status in ('1', '100'):
            custom = parsed_data.get('custom')
            amount = parsed_data.get('received_amount')
            currency = parsed_data.get('currency2')
            pairs = custom.split(',')
            data = {key.strip('"'): value.strip('"') for key, value in (pair.split(':') for pair in pairs)}
            telegram_id = data.get('telegramId')
            duration = data.get('duration')
            processedPayments.add(transaction_id)
            await add_transaction(transaction_id, 'SUCCESS', amount, currency, 'CoinPayments', duration, telegram_id, "Unknown")
            await add_user_to_group(user_id=telegram_id, duration=duration)
            return jsonify({"message": "Verification Success"}), 200
        else:
            return jsonify({"message": "Status incomplete"}), 200

    except Exception as e:
        return jsonify({"message": "Verification failed: "}), 400