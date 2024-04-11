import asyncio
import time
from telegram.ext import CommandHandler,filters,MessageHandler
import os
from config.Database import pool
from bot.userManagment import execute_query
from config.config_management import config_manager
BOTID=os.getenv("botId")
ADMINID=int(config_manager().get_metadata_config()["adminId"])
async def broadcast_start(update,context):
    try:
        chat_id = update.message.chat_id 
        query=(f'SELECT "telegramId" fROM customer WHERE "botId"=\'{BOTID}\'')
        if(chat_id==ADMINID):
            rows =await execute_query(query=query,fetch=True)
            global broadcast_chatid
            broadcast_chatid=[]
            for row in rows:
                broadcast_chatid.append(row[0])
            await context.bot.send_message(chat_id=update.message.chat_id, text='send The message you would like to broadcast please send it precisely')
            global messx
            messx=MessageHandler(filters.VIDEO | filters.PHOTO | filters.TEXT, broadcast_message)
            dp.add_handler(messx)
    except Exception as e:
        print(e)

async def broadcast_message(update, context):
    chat_id = update.message.chat_id
    if chat_id ==ADMINID:
        try:
            message = update.message
            caption = message.caption
            text = message.text if message.text else None
            photo = message.photo if message.photo else None
            video = message.video if message.video else None

            async def send_message_to_user(i):
                nonlocal count, fail
                try:
                    if photo:
                        await context.bot.send_photo(chat_id=int(i), photo=photo[-1].file_id, caption=caption)
                    elif video:
                        await context.bot.send_video(chat_id=int(i), video=video.file_id, caption=caption)
                    elif text:
                        await context.bot.send_message(chat_id=int(i), text=message.text)
                    count += 1
                except Exception as e:
                    fail += 1

            count = 0
            fail = 0
            start_time = time.time()
            tasks = [send_message_to_user(i) for i in broadcast_chatid]
            await asyncio.gather(*tasks)
            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time
            await context.bot.send_message(chat_id=ADMINID,
                                           text=f"Messages were successfully sent to {count} people and unsuccessfully to {fail} people and it was completed in{elapsed_time}")
            dp.remove_handler(messx)

        except Exception as e:
            await context.bot.send_message(chat_id=ADMINID, text=f"Broadcast message failed: {str(e)}")

def Broadcastermain(dpw):
    global dp
    dp=dpw
    dp.add_handler(CommandHandler('broadcast',broadcast_start))