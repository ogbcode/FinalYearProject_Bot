import base64
import hashlib
import hmac
import json
import re
import time
import uuid
import httpx
from Crypto.Signature import pkcs1_15
from quart import jsonify, request
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from dotenv import load_dotenv
from config.quartServer import app
from bot.userManagment import add_user_to_group
from config.config_management import config_manager

metadata=config_manager().get_metadata_config()

def random_alphanumeric_string():
    random_uuid = str(uuid.uuid4()).replace("-", "")[:6]
    return random_uuid

def get_timestamp():
    return int(time.time() * 1000)

def random_string():
    random = str(uuid.uuid4())
    random = random.replace("-", "")
    return random[0:32]

__version__="1.0.0"


def hashing(secrect: str, to_hashing: str):
    return (
        hmac.new(secrect.encode("utf-8"), to_hashing.encode("utf-8"), hashlib.sha512)
        .hexdigest()
        .upper()
    )

async def send_signed_request(chat_id,amount,duration,api_key=None, secret_key=None):
    merchant_trade_no = f"id{chat_id}bPay{random_alphanumeric_string()}dur{duration}"
    payload={
    "env": {
        "terminalType": "APP"
    },
    "merchantTradeNo": merchant_trade_no,
    "orderAmount":amount,
    "currency": "USDT",
    #   "orderExpireTime":"3600000000000",
    "returnUrl":metadata['success_url'],
    "description": metadata['description'],
    "webhookUrl":f"{metadata['domain']}/binancepay",
    "goodsDetails": [{
        "goodsType": "02",
        "goodsCategory": "7000",
        "referenceGoodsId": "7876763A3B",
        "goodsName": metadata['name'],
        "goodsDetail": metadata['description'],
    }]
    }
    url_path="/binancepay/openapi/v3/order"
    base_url='https://bpay.binanceapi.com'
    timestamp = get_timestamp()
    nonce = random_string()
    payload_to_sign = (
        str(timestamp) + "\n" + nonce + "\n" + json.dumps(payload) + "\n")
    signature = hashing(secret_key, payload_to_sign)
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "User-Agent": "binance-pay-connector/" + __version__,
        "BinancePay-Timestamp": str(timestamp),
        "BinancePay-Nonce": nonce,
        "BinancePay-Certificate-SN":api_key,
        "BinancePay-Signature": signature,
    }
    url =base_url+url_path
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
    try:
        data = response.json()
    except ValueError:
        data = response.text

    return data

def verify_binance_pay_webhook(timestamp,nonce,signature,payload):
        binance=config_manager().get_binance_config()
        binance_pay_headers = {
            'BinancePay-Timestamp': timestamp,
            'BinancePay-Nonce': nonce,
            'BinancePay-Signature': signature,
        }

        payload_to_sign = f"{binance_pay_headers['BinancePay-Timestamp']}\n{binance_pay_headers['BinancePay-Nonce']}\n{payload}\n"
        local_signature = SHA256.new(payload_to_sign.encode('utf-8'))
        pub_key = RSA.import_key(binance["binance_publickey"])
        binance_signature = base64.b64decode(binance_pay_headers['BinancePay-Signature'])
        try:
            pkcs1_15.new(pub_key).verify(local_signature, binance_signature)
            return True
        except:
            return False



# result = send_signed_request(amount=0.00001,key=api_key, secret=secretkey)
# formatted_result = json.dumps(result, indent=4)
# print(formatted_result)
processedPayments=set()
@app.route('/binancepay', methods=['POST'])
async def binacepayWebhook():
    try:
        timestamp=request.headers.get('BinancePay-Timestamp')
        nonce=request.headers.get('BinancePay-Nonce')
        signature=request.headers.get('BinancePay-Signature')
        payload = await request.get_data(as_text=True)
        if not all([timestamp, nonce, signature,payload]):
            return jsonify({"message": "Bad Request"}),400
        if not  verify_binance_pay_webhook(timestamp,nonce,signature,payload):
            return jsonify({"message": "Verification failed"}), 400
        
        data=await request.get_json()
        paymentStatus = data["bizStatus"]

        if (paymentStatus=="PAY_SUCCESS"):
            merchant_trade_no = json.loads(data["data"])["merchantTradeNo"]
            if merchant_trade_no in processedPayments:
                return jsonify({"message": "Payment already processed"}), 200
            chatid_match = re.search(r'id(\d+)', merchant_trade_no)
            chatid = chatid_match.group(1)
            dur_number_match = re.search(r'dur(\d+)',merchant_trade_no)
            duration = dur_number_match.group(1)
            if await add_user_to_group(user_id=chatid,duration=duration):
                processedPayments.add(merchant_trade_no)
                return jsonify({"message": "Verification success"}), 200
            else :
                return jsonify({"message": "Verification succes but failed to add user"}), 200
        elif(paymentStatus=="PAY_CLOSED"):
            return jsonify({"message": "Payment Timed out"}), 200
    except:
        return jsonify({"message": "Internal Server Error"}),500
    
    