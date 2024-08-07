import hashlib
import json
import os
import requests
from telegram import InlineKeyboardButton
from config.quartServer import backend_url
from Crypto.Cipher import AES

def create_hash(bot_id: str):
    token='ChidubemRailway234'
    data_to_hash = f"{bot_id}{token}"
    hash_object = hashlib.sha256()
    hash_object.update(data_to_hash.encode())
    hashed_data = hash_object.hexdigest()
    return hashed_data
class ConfigurationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_connection):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.db_connection = db_connection
            self.config_cache = {}
            self._initialize_config_cache()

    def _initialize_config_cache(self):
        for key in self.db_connection.get_all_keys():
            config_data = self._retrieve_config_from_db(key)
            if config_data:
                self.config_cache[key] = config_data

    def __get_config(self, key):  # Modified to make it private
        if key in self.config_cache:
            return self.config_cache[key]
        else:
            return None

    def _retrieve_config_from_db(self, key):
        config_data = self.db_connection.get(key)
        return config_data if config_data else None

    # Method to get metadata configuration data
    def get_metadata_config(self):
        return {
            'adminId': self.__get_config('adminId'),
            'domain': self.__get_config('domain'),
            'groupchatId': self.__get_config('groupchatId'),
            'customersupport_telegram': self.__get_config('customersupport_telegram'),
            'name': self.__get_config('name'),
            'description': self.__get_config('description'),
            'success_url': self.__get_config('success_url'),
            'twoweeks_price': self.__get_config('twoweeks_price'),
            'onemonth_price':  self.__get_config('onemonth_price'),
            'lifetime_price': self.__get_config('lifetime_price'),
            'subscription_benefits':self.__get_config('subscription_benefits')
            
        }

    # Method to get Binance configuration data
    def get_binance_config(self):
        return self.__get_config('binance')

    # Method to get Coinpayment configuration data
    def get_coinpayment_config(self):
        return self.__get_config('coinpayment')

    # Method to get Nowpayment configuration data
    def get_nowpayment_config(self):
        return self.__get_config('nowpayment')

    def get_stripe_config(self):
        return self.__get_config('stripe')

    # Method to get Paystack configuration data
    def get_paystack_config(self):
        return self.__get_config('paystack')

    # Method to get Telegram configuration data
    def get_telegram_config(self):
        return self.__get_config('telegram')

    # Method to get Crypto Address configuration data
    def get_crypto_address_config(self):
        return self.__get_config('crypto_address')
    def get_available_bank_methods(self):
        available_methods = []
        if self.__get_config('stripe'):
            available_methods.append([InlineKeyboardButton("💳 Stripe", callback_data='Payment(Stripe)')])

        if self.__get_config('paystack'):
            available_methods.append([InlineKeyboardButton("🏦 Paystack", callback_data='Payment(Paystack)')])
       
        return available_methods
    def get_available_crypto_methods(self):
        available_methods = []
        if self.__get_config('binance'):
            available_methods.append([InlineKeyboardButton("💰 Binance Pay", callback_data='Payment(BinancePay)')])
        if self.__get_config('coinpayment'):
            available_methods.append([InlineKeyboardButton("💱 Coinpayment", callback_data='Payment(Coinpayment)')])

        if self.__get_config('nowpayment'):
            available_methods.append([InlineKeyboardButton("💲 Nowpayment", callback_data='Payment(Nowpayment)')])

        # if self.__get_config('crypto_address'):
        #     # available_methods.append([InlineKeyboardButton("⚡️ BTC (Bitcoin)", callback_data='Payment(CryptoBTC)')])
        #     available_methods.append([InlineKeyboardButton("💲 USDT (TRC20)", callback_data='Payment(CryptoUSDT)')])

        return available_methods

class DbData:
    def __init__(self, database):
        self.database = database

    def get_all_keys(self):
        return self.database.keys()

    def get(self, key):
        return self.database.get(key)


def decrypt_data(encrypted_text):
    try:
        IV_LENGTH = 16
        key = os.getenv('ENCRYPTION_KEY')  # This should be replaced with os.getenv('ENCRYPTION_KEY')
        iv = bytes.fromhex(encrypted_text[:IV_LENGTH * 2])
        encrypted = bytes.fromhex(encrypted_text[IV_LENGTH * 2:])
        cipher = AES.new(key.encode(), AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)
        decrypted = decrypted[:-decrypted[-1]].decode('utf-8')
        return decrypted
    except Exception as e:
        print("Error decrypting data:", str(e))
        return None


def config_manager():
    botId = os.getenv("botId") #replace with env file
    if ConfigurationManager._instance is None:
        headers = {
        "Authorization": f"{create_hash(botId)}",
   
    }
        response = requests.get(f"{backend_url}/backend/v1/bot/data/"+botId,headers=headers) # replace with env file
        if response.status_code == 200:
            encrypted_text = response.json()['data']
            db_connection = DbData(json.loads(decrypt_data(encrypted_text)))
            
            ConfigurationManager._instance = ConfigurationManager(db_connection)
        else:
            return("Failed to retrieve data. Status code:", response.status_code)
    return ConfigurationManager._instance


