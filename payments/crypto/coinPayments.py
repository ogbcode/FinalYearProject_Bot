import hashlib
import hmac
from urllib.parse import urlencode
import requests
from pycoinpayments.coinpayments import CoinPayments
# Replace these values with your actual CoinPayments API keys
PUBLIC_KEY = '7611885e49b716358f604492f60d94b98c1f2a96fad7ac08b3ff553a5b3caf2e'
PRIVATE_KEY = 'C7a227053f7015C49d9Cd8a9317867Af90701b6E8f10aacb0D5feF7ff909383c'
MERCHANT_ID = 'a14cccbbfe6a4da708a97d54213d80b2'
IPN_SECRET = 'chidubem'
CALLBACK_URL='https://f7de-102-88-63-176.ngrok-free.app'
COINPAYMENTS_API_URL = 'https://www.coinpayments.net/api.php'

def generate_hmac(data, secret_key):
    hmac_object = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha512)
    return hmac_object.hexdigest()

def make_api_call(command, extra_params=None):
    main_fields = {
        'version': '1',
        'key': PUBLIC_KEY,
        'cmd': command,
    }

    if extra_params:
        main_fields.update(extra_params)

    raw_data =urlencode(main_fields)
    hmac_signature = generate_hmac(raw_data, PRIVATE_KEY)
    
    headers = {'HMAC': hmac_signature}

    response = requests.post(COINPAYMENTS_API_URL, data=main_fields, headers=headers)

    if response.ok:
        result = response.json()
        print("API Response:", result)
    else:
        print(f"Error: {response.status_code}, {response.text}")

create_payment_params = {
    'amount': 1,
    'currency1': 'USD',#passed by code
    'currency2': 'BTC', #passed by code
    'buyer_email': 'chidteubemogbuefi@gmail.com',#passed by code
    'item_name': 'test',
    'ipn_url': CALLBACK_URL,
    'success_url': 'https://your-success-url.com/',
    'cancel_url': 'https://your-cancel-url.com/'
}

make_api_call('create_transaction', create_payment_params)