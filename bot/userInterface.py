import asyncio
from datetime import datetime
import re
import os
import time
import uuid

import requests

from config.Database import pool
import logging
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler,CallbackQueryHandler
from telegram import Update

from config.config_management import config_manager
from config.quartServer import backend_url

if config_manager().get_paystack_config():
    from payments.banks.Paystack import create_paystack_checkout

if config_manager().get_stripe_config():
    from payments.banks.Stripe import create_stripe_checkout

if config_manager().get_binance_config():
    from payments.crypto.binancePay import send_signed_request

if config_manager().get_coinpayment_config():
    from payments.crypto.coinPayments import create_coinpayment_transaction

if config_manager().get_nowpayment_config():
    from payments.crypto.nowPayments import create_nowpayment_invoice

TWOWEEKPRICE=config_manager().get_metadata_config()['twoweeks_price']
ONEMONTHPRICE=config_manager().get_metadata_config()['onemonth_price']
LIFETIMEPRICE=config_manager().get_metadata_config()['lifetime_price']
CUSTOMERSUPPORT=config_manager().get_metadata_config()['customersupport_telegram']
BENEFITS=config_manager().get_metadata_config()["subscription_benefits"]
BANKPAYMENT=config_manager().get_available_bank_methods()
CRYPTOPAYMENT=config_manager().get_available_crypto_methods()
# print(PAYMENTMETHODS)
COMMAND, INPUT = range(2)
COMMAND2, INPUT2 = range(2)
BOTID=os.getenv("botId")
USERID=os.getenv("userId")

async def user_exists_in_database(chatid):
    try:
        # query = 'SELECT * FROM customer WHERE "telegramId" = %s AND "botId" =%s'
        # values = [str(chatid),BOTID]
        # result=await execute_query(query,values,True)
        # if(bool(result)):
        #     return True
        # else:
        #     return False
        url=f"{backend_url}/backend/v1/customers/telegram/bot"
        data={"telegramId":chatid,"botId":BOTID}
        result=requests.get(url,data=data)
        if(result.status_code==200):
            return True
        else:
            return False
    except Exception as e:
        # print(e)
        return False

async def insert_into_database(firstname, chatid):
    try:
        if await user_exists_in_database(chatid):
            pass  # User already exists, no need to insert
        else:
            # query = 'INSERT INTO customer ("id","firstName", "telegramId","userId", "botId", "createdAt", "updatedAt") VALUES  (%s, %s,%s,%s,%s,%s,%s)'
            # now = datetime.now()
            # values = [str(uuid.uuid4()),str(firstname), str(chatid),USERID,BOTID,now,now]
            # await execute_query(query,values)
            url=f"{backend_url}/backend/v1/customers/create"
            data={"firstName":firstname,"telegramId":str(chatid),"userId":USERID,"botId":BOTID}
            requests.post(url,data=data)
    except Exception as e:
        # pass
        print(e)
async def start_command(update:Update,context):
    firstname=update.message.chat.first_name
    chatid=update.effective_chat.id
    await(insert_into_database(firstname,chatid))
    services= [  [InlineKeyboardButton(f"Membership ${TWOWEEKPRICE}/2 weeks ", callback_data=f'VIP ${TWOWEEKPRICE} (2weeks)')],
                 [InlineKeyboardButton(f"Membership ${ONEMONTHPRICE}/1 Month " , callback_data=f'VIP ${ONEMONTHPRICE} (1month)')],
                 [InlineKeyboardButton(f"Membership ${LIFETIMEPRICE}/Lifetime ", callback_data=f'VIP ${LIFETIMEPRICE} (lifetime)')]]
                #  [InlineKeyboardButton("PROPFIRM ACCOUNT PASSING 🚨", callback_data= "PASSAGE")]]
    reply_markup = InlineKeyboardMarkup(services)
    
    logging.info(f"{firstname} started the bot.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! " +firstname)
    if(BENEFITS==""):
        user_benefits="Premium service"
    else:
        user_benefits=BENEFITS
    await update.message.reply_text(f"""{config_manager().get_metadata_config()["name"]}
    
Your Benefits:
{user_benefits}
    """, reply_markup=reply_markup)

async def service_callback(update,context):
    query = update.callback_query
    planselected = query.data
    context.user_data['planselected'] =planselected
    if(planselected==f'VIP ${TWOWEEKPRICE} (2weeks)'):
        duration=14
    if(planselected==f'VIP ${ONEMONTHPRICE} (1month)'):
        duration= 30
    if(planselected==f'VIP ${LIFETIMEPRICE} (lifetime)'):
        duration=99999
    context.user_data['duration'] =duration

    paymentmethods = [#*PAYMENTMETHODS,  # Include the payment methods obtained from config_manager
    [InlineKeyboardButton("💳Bank", callback_data='Payment(Bank)')],
    [InlineKeyboardButton("⚡️Crypto", callback_data='Payment(Crypto)')],
    [InlineKeyboardButton("🔑Access Code", callback_data='AccessCode')],
    [InlineKeyboardButton("<<<Back ", callback_data='Back')],
]

    payment_markup = InlineKeyboardMarkup(paymentmethods)
    trial=planselected.split()
    context.user_data['price'] = trial[1]
    match = re.search(r'\((.*?)\)', trial[2])
    period = match.group(1)
    await query.edit_message_text(text=f'Your benefits:\n✅*VIP*\(Channel Access\)\n\nPrice:*{trial[1]}*\nBilling Period:*{period}*\nBilling Mode:*Non recurring* ', reply_markup=payment_markup,parse_mode='MarkdownV2')

async def crypto_callback_menu(update, context):
    query = update.callback_query
    paymentmethods = [*CRYPTOPAYMENT,  # Include the payment methods obtained from config_manager
    [InlineKeyboardButton("<<<Back ", callback_data='Back')]]
    payment_markup = InlineKeyboardMarkup(paymentmethods)
    planselected = context.user_data.get('planselected', '')
    trial=planselected.split()
    match = re.search(r'\((.*?)\)', trial[2])
    period = match.group(1)
    await query.edit_message_text(text=f'Your benefits:\n✅*VIP*\(Channel Access\)\n\nPrice:*{trial[1]}*\nPayment Method:Crypto\nBilling Period:*{period}*\nBilling Mode:*Non recurring* ', reply_markup=payment_markup,parse_mode='MarkdownV2')

async def bank_callback_menu(update, context):
    query = update.callback_query
    paymentmethods = [*BANKPAYMENT,  # Include the payment methods obtained from config_manager
    [InlineKeyboardButton("<<<Back ", callback_data='Back')]]
    payment_markup = InlineKeyboardMarkup(paymentmethods)
    planselected = context.user_data.get('planselected', '')
    trial=planselected.split()
    match = re.search(r'\((.*?)\)', trial[2])
    period = match.group(1)
    await query.edit_message_text(text=f'Your benefits:\n✅*VIP*\(Channel Access\)\n\nPrice:*{trial[1]}*\nPayment Method:Bank\nBilling Period:*{period}*\nBilling Mode:*Non recurring* ', reply_markup=payment_markup,parse_mode='MarkdownV2')



async def Crypto_payment_callback(update, context):
    query = update.callback_query
    # first_name = update.callback_query.from_user.first_name
    # last_name = update.callback_query.from_user.last_name if update.callback_query.from_user.last_name else ''
    planselected = context.user_data.get('planselected', '')
    duration= context.user_data.get('duration', '')
    payment_method= query.data
    chatid=update.effective_chat.id
    priceDollars = context.user_data.get('price', '')
    priceSplit = priceDollars.split('$')[1]
    price = int(priceSplit)

    if (payment_method=='Payment(Nowpayment)'):
        url=await create_nowpayment_invoice(update.effective_chat.id,duration,price)
        button = InlineKeyboardButton(text="⚡️ Subscribe", url=url)
        subscribe_markup = InlineKeyboardMarkup([[button]])
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please click the button below:", reply_markup=subscribe_markup)
    if (payment_method=='Payment(BinancePay)'):
        
        data=await send_signed_request(chat_id=chatid,amount=price,duration=duration,api_key=config_manager().get_binance_config()["binance_apikey"],secret_key=config_manager().get_binance_config()["binance_secretkey"])
        qrcodePhoto= data['data']['qrcodeLink']
        link_text = 'Open Binance app to complete payment '
        deeplink_url = data['data']['universalUrl']
        message_text = f'<a href="{deeplink_url}">{link_text}</a>'+'\n\nOR'+'\n\nScan the Qr code below to complete the payment.(valid for only 1 hour) '
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, parse_mode=ParseMode.HTML,disable_web_page_preview=True)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=qrcodePhoto)

    if (payment_method=='Payment(CryptoBTC)'):
        trial=planselected.split()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Send {trial[1]} for the {trial[0]} {trial[2]} plan to this BTC(Bitcoin) address\n\n Send the Transaction Receipt✅ to "+ CUSTOMERSUPPORT)
        await context.bot.send_message(chat_id=update.effective_chat.id,text=config_manager().get_crypto_address_config()["usdt_address"])

    if (payment_method=='Payment(CryptoUSDT)'):
        trial=planselected.split()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Send {trial[1]} for the {trial[0]} {trial[2]} plan to this USDT TRC20 address\n\n Send the Transaction Receipt✅ to "+ CUSTOMERSUPPORT)
        await context.bot.send_message(chat_id=update.effective_chat.id,text=config_manager().get_crypto_address_config()["btc_address"])
async def coinpayment_handler(update,context):
    duration= context.user_data.get('duration', '')
    email = update.message.text
    chat_id=update.effective_chat.id
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    priceDollars = context.user_data.get('price', '')
    priceSplit = priceDollars.split('$')[1]
    price = int(priceSplit)

    if re.match(email_pattern, email):
        transaction=create_coinpayment_transaction(chat_id,duration,price,email)
        amount = transaction['amount']
        blockchain = 'Litecoin Testnet'
        status_url=transaction['transaction_status']
        qrcodePhoto=transaction['qr_code']
        address=transaction['address']
        transaction_status_link = f'<a href="{status_url}">Transaction Status</a>'
        message_text = f"Please send {amount} LTCT ({blockchain}) (exact amount, after commissions) to the following address:\n\n{address}\n\nThis unique address is valid only for 1 hour. Your payment will be processed by CoinPayments.\n\nYou can check your transaction status here.\n\n{transaction_status_link}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, parse_mode=ParseMode.HTML,disable_web_page_preview=True)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=qrcodePhoto)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid email address")
        return ConversationHandler.END
        

async def paystack_handler(update,context):
    duration= context.user_data.get('duration', '')
    email = update.message.text
    first_name = update.message.from_user.first_name
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    priceDollars = context.user_data.get('price', '')
    priceSplit = priceDollars.split('$')[1]
    price = int(priceSplit)
    if re.match(email_pattern, email):
        url=await create_paystack_checkout(update.effective_chat.id,first_name,email,price,duration)
        button = InlineKeyboardButton(text="💳 Subscribe", url=url)
        subscribe_markup = InlineKeyboardMarkup([[button]])
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please click the button below:", reply_markup=subscribe_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Invalid email address.")
        return ConversationHandler.END
       

async def stripe_handler(update,context):
    duration= context.user_data.get('duration', '')
    priceDollars = context.user_data.get('price', '')
    priceSplit = priceDollars.split('$')[1]
    price = int(priceSplit)
    url=await create_stripe_checkout(update.effective_chat.id,duration,price)
    button = InlineKeyboardButton(text="💳 Subscribe", url=url)
    subscribe_markup = InlineKeyboardMarkup([[button]])
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please click the button below:", reply_markup=subscribe_markup)

async def Back_command(update,context):
    query = update.callback_query
    services= [  [InlineKeyboardButton(f"Membership ${TWOWEEKPRICE}/2 weeks ", callback_data=f'VIP ${TWOWEEKPRICE} (2weeks)')],
                 [InlineKeyboardButton(f"Membership ${ONEMONTHPRICE}/1 Month " , callback_data=f'VIP ${ONEMONTHPRICE} (1month)')],
                 [InlineKeyboardButton(f"Membership ${LIFETIMEPRICE}/Lifetime ", callback_data=f'VIP ${LIFETIMEPRICE} (lifetime)')]]
    reply_markup = InlineKeyboardMarkup(services)
    if(BENEFITS==""):
        user_benefits="Premium service"
    else:
        user_benefits=BENEFITS
    await query.edit_message_text(text=f"""{config_manager().get_metadata_config()["name"]}
    
Your Benefits:
{user_benefits}""", reply_markup=reply_markup)

async def help_command(update,context):
    await update.message.reply_text(f"Please contact {CUSTOMERSUPPORT} For more payment options or any issues faced")

async def start_email(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,text="Please send your email address.")
    return INPUT

async def start_email2(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,text="Please send your email address.")
    return INPUT2


    
     
def userInterface_main(dp):
    conv_handler_paystack = ConversationHandler(
    entry_points=[(CallbackQueryHandler(start_email, pattern=r'Payment\(Paystack\)'))],
    states={
        INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, paystack_handler)],
    },
    fallbacks=[]
)
    conv_handler_coinpayment = ConversationHandler(
    entry_points=[(CallbackQueryHandler(start_email2, pattern=r'Payment\(Coinpayment\)'))],
    states={
        INPUT2: [MessageHandler(filters.TEXT & ~filters.COMMAND, coinpayment_handler)],
    },
    fallbacks=[]
)
    dp.add_handler(conv_handler_paystack)
    dp.add_handler(conv_handler_coinpayment)
    dp.add_handler(CommandHandler("start",start_command))
    dp.add_handler(CommandHandler("help",help_command))
    dp.add_handler(CallbackQueryHandler(Back_command,pattern=re.compile(r'\b\w*Back\w*\b')))
    dp.add_handler(CallbackQueryHandler(service_callback,pattern = re.compile(r'\b\w*VIP\w*\b')))
    dp.add_handler(CallbackQueryHandler(stripe_handler,pattern=re.compile(r'Payment\(Stripe\)')))
    dp.add_handler(CallbackQueryHandler(crypto_callback_menu,pattern=re.compile(r'Payment\(Crypto\)')))
    dp.add_handler(CallbackQueryHandler(bank_callback_menu,pattern=re.compile(r'Payment\(Bank\)')))