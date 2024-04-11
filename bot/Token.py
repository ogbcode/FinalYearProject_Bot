import asyncio
import os
import time
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler,CallbackQueryHandler
from cryptography.fernet import Fernet
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.Database import pool
from bot.userManagment import add_user_to_group
from config.config_management import config_manager
fernet_key =Fernet.generate_key()
fernet = Fernet(fernet_key)
COMMAND, INPUT = range(2)
revoked_tokens=[]

async def tokenreset():
    while True:
        global fernet_key, fernet, revoked_tokens
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        revoked_tokens.clear()
        await asyncio.sleep(43200)

def encrypt_data(data):
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data


def decrypt_data(token):
    decrypted_data = fernet.decrypt(token)
    return decrypted_data.decode()

async def tokenstart(update, context):
    if (update.effective_chat.id==int(config_manager().get_metadata_config()["adminId"])):
        # Create an inline keyboard with duration options
        keyboard = [[InlineKeyboardButton("2 Weeks", callback_data='14')],
                    [InlineKeyboardButton("1 Month", callback_data='30')],
                    [InlineKeyboardButton("Lifetime", callback_data='99999')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the keyboard to the user
        await context.bot.send_message(chat_id=update.message.chat_id,
                                text="Please select a membership duration:",
                                reply_markup=reply_markup)

async def generatetoken(update, context):
    query = update.callback_query
    duration_option = query.data
    membership_days = int(duration_option)

    chat_id = query.message.chat_id
    data = f"{membership_days}"
    encrypted_token = encrypt_data(data)

    await context.bot.send_message(chat_id=chat_id,
                             text=f"{encrypted_token.decode()}")


async def startdecryption(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,text="Please send the token.")
    return INPUT

async def decrypt(update, context):
    encrypted_token = update.message.text
    encrypted_token_bytes = encrypted_token.encode()
    if encrypted_token in revoked_tokens:
        await context.bot.send_message(chat_id=update.message.chat_id, text="This token has been used.")
    else:
        try:
            decrypted_data = decrypt_data(encrypted_token_bytes)
            asyncio.create_task(add_user_to_group(user_id=update.message.chat_id,first_name=update.message.from_user.first_name,duration=decrypted_data))
            revoked_tokens.append(encrypted_token)
        except Exception as e:
            print(e)
            await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid or corrupted token!")
    return ConversationHandler.END



def Token_main(dp):
    
    asyncio.create_task(tokenreset())
    
    dp.add_handler(CommandHandler("tokenstart",tokenstart))
    conv_handler = ConversationHandler(
        entry_points=[(CallbackQueryHandler(startdecryption, pattern=r'\bAccessCode\b'))],
        states={
            INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, decrypt)],
        },
        fallbacks=[]
    )
    dp.add_handler(CallbackQueryHandler(generatetoken,
                                    pattern='^(14|30|99999)$'))
    dp.add_handler(conv_handler)

