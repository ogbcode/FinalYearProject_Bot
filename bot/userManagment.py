import asyncio
import time
import uuid
import pymysql
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
from telegram.ext import CommandHandler,MessageHandler,filters
from config.Database import pool
from config.config_management import config_manager
GROUPCHATID =int(config_manager().get_metadata_config()["groupchatId"])
ADMINID=int(config_manager().get_metadata_config()["adminId"])
BOTID=os.getenv("botId")
def get_image_stream():
    # Deployed
    image_path ="vip.jpg"
    # local
    # image_path=r"C:\Users\tradi\Documents\PROJECTS\FINAL YEAR PROJECT\TelegramBot\Telegram_bot\vip.jpg"

    image = Image.open(image_path)
    image_stream = BytesIO()
    image.save(image_stream, format="JPEG")
    image_stream.seek(0)
    return image_stream

async def execute_query(query, values=None, fetch=False):
    try:
        with pool.getconn() as conn:
            with conn.cursor() as cursor:
                if values:
                    cursor.execute(query, values)
                else:
                    cursor.execute(query)
                conn.commit()
                if fetch:
                    return cursor.fetchall()
    except Exception as e:
        print(e)
        return None
    finally:
        if conn:
            pool.putconn(conn)
# Add a user to the group by invite link
async def add_transaction(
    transaction_id: str,
    status: str,
    amount:str,
    currency: str,
    platform: str,
    duration:str,
    telegarmId: str,
):
    # query='SELECT "id"  from customer where "telegramId"=%s AND "botId"=%s'
    # values=(telegarmId,BOTID)
    # result=await execute_query(query,values,True)
    # id = str(uuid.uuid4())
    # customer_id=result[0][0]
    # date = datetime.now()
    # query='INSERT INTO transaction( "id", "transactionId", "status", "amount", "currency", "platform", "duration", "createdAt", "updatedAt", "customerId") VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)'
    # values=(id,transaction_id,status,amount,currency,platform,duration,date,date,customer_id)
    # url=f"{os.getenv('domain')}/backend/v1/customers/telegram/bot"
    url=f"{os.getenv("domain")}/backend/v1/transaction/create"
    data={"transactionId":transaction_id,"status":status,"amount":amount,"currency":currency,"platform":platform,"duration":duration,"telegramId":telegarmId,"botId":BOTID}
    requests.post(url,data=data)

async def add_user_to_group(user_id,first_name=None,duration=None):
    try:
        int(user_id)
        if not first_name:
            chat_info = await bot.get_chat(user_id)
            first_name = chat_info.first_name if chat_info else None
        
        expireTime=(datetime.utcnow() + timedelta(minutes=5))
        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUPCHATID,
            expire_date=expireTime,
            member_limit=1
        )
        succesfull= InlineKeyboardButton(text="Join The VIP Group", url=invite_link.invite_link)
        succesful_markup = InlineKeyboardMarkup([[succesfull]])
        query=('SELECT * from  subscriber WHERE "telegramId"=%s AND "botId"=%s')
        values=(str(user_id),BOTID)
        rows=await execute_query(query,values,True)
        if rows:
                query=('SELECT "joinDate","duration","expiryDate" from subscriber where "telegramId"=%s AND "botId"=%s')
                values=(str(user_id),BOTID)
                result=await execute_query(query,values,True)
                userDuration=result[0][1]
                userJoindate=result[0][0]
                userExpirydate=result[0][2]
                if userJoindate:
                    query= 'UPDATE subscriber SET "duration" = %s, "expiryDate" = %s WHERE "telegramId" = %s AND "botId" = %s'
                    given_date = datetime.strptime(userExpirydate, "%Y-%m-%d")
                    new_date = given_date + timedelta(days=int(duration))
                    new_date_str = new_date.strftime("%Y-%m-%d")
                    values=(str(int(userDuration)+int(duration)),new_date_str,str(user_id),BOTID)
                    await execute_query(query,values)
                    await bot.send_message(chat_id=user_id, text=f'Your Payment was successful✅.{duration} days has been added to your Subscription.')
           
                    return True
                else:
                    query = ('UPDATE subscriber SET "duration" = %s WHERE "telegramId" = %s AND "botId" = %s')
                    values=(str(int(userDuration)+int(duration)),str(user_id),BOTID)
                    await execute_query(query,values)
                    await bot.send_photo(chat_id=user_id, photo=get_image_stream(), caption='Your Payment was successful.Join the group to activate your subscription📈', reply_markup=succesful_markup)
                    return True

        else:
            now = datetime.now()
            query=('INSERT INTO subscriber ("id", "firstName", "telegramId", "joinDate", "expiryDate", "active", "duration", "createdAt", "updatedAt", "botId") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
            values=(str(uuid.uuid4()),str(first_name),str(user_id),"","","FALSE",str(duration),now,now,BOTID)   
            with pool.getconn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query,values)
                conn.commit()
            await bot.send_photo(chat_id=user_id, photo=get_image_stream(), caption='Your Payment was successful.Join the group to activate your subscription📈', reply_markup=succesful_markup) 
            return True
 
    except Exception as e:
        print(e)
        await bot.send_message(chat_id=user_id, text="Error while adding you to the group")
        return False
    
    # remove subscripers with expired subscription
async def remove_expiredsubscribers():
    query=('SELECT * FROM subscriber WHERE "active" =%s AND "botId" = %s')
    values=('TRUE',BOTID)
    rows=await execute_query(query,values,True)
    if rows:
        for i in rows:
            chatid=int(i[2])
            username=i[1]
            expiry_date= datetime.strptime(i[4],'%Y-%m-%d')
            timeleft=expiry_date-datetime.now()
            if timeleft<=timedelta(days=0):
                try:
                    try:
                        query=('DELETE FROM subscriber WHERE "telegramId"=%s AND "botId"=%s')
                        values=(str(chatid),BOTID)
                        await execute_query(query,values)
                        await bot.kick_chat_member(chat_id=GROUPCHATID, user_id=chatid)
                        await bot.send_message(chat_id=chatid, text = "Your INNER ⭕️ membership subscription has expired, and you have been removed from the group. Click 👉👉👉 /start 👈👈👈 to renew and regain access!")
                        await bot.send_message(chat_id=int(ADMINID), text=f"User {username} subscription has expired and has been removed from the group✅")
                    except:
                        await bot.kick_chat_member(chat_id=GROUPCHATID, user_id=chatid)
                        await bot.send_message(chat_id=chatid,text = "Your INNER ⭕️ membership subscription has expired, and you have been removed from the group. Click 👉👉👉 /start 👈👈👈 to renew and regain access!"
    )
                        await bot.send_message(chat_id=int(ADMINID), text=f"User {username} subscription has expired and has been removed from the group✅")
                except Exception as e:
                    print(e)
                    continue
            else:
                pass
# Tell members their subscription is about to expire
async def membershipwarning():
    query=('SELECT * FROM subscriber WHERE "active" =%s AND "botId" = %s')
    values=('TRUE',BOTID)
    rows=await execute_query(query,values,True)
    if rows:
        for i in rows:
            chatid=int(i[2])
            expiry_date= datetime.strptime(i[4],'%Y-%m-%d')
            timeleft=expiry_date-datetime.now()
            if timedelta(days=0)<timeleft<=timedelta(days=3):
                try:
                    timeleft=str(timeleft)
                    daysleft=timeleft.split(",")
                    await bot.send_message(chat_id=chatid, text="Reminder you have" + " "+ daysleft[0] +" "+ "in the INNER ⭕️!\n Click /start To renew it and rollover your subscription")
                except:
                    continue
# check all active member in a group
async def check_activemebers():
    query= ('SELECT * FROM subscriber WHERE "active" =%s AND "botId" = %s')
    values=('TRUE',BOTID)
    rows=await execute_query(query,values,True)
    if rows:
        for i in rows:
            username=i[1]
            member_chatid=i[2]
            expiry_date= datetime.strptime(i[4],'%Y-%m-%d')
            timeleft=expiry_date-datetime.now()
            timeleft=str(timeleft)
            daysleft=timeleft.split(",")
            time_days=daysleft[0].split("days")
            years = int(time_days[0]) //365
            days = int(time_days[0]) % 365
            if(years==0):
                await bot.send_message(chat_id=int(ADMINID),  text=f"{username} has {days} days left in the group (Chat ID: {member_chatid}) ✅")
            else:
                await bot.send_message(chat_id=int(ADMINID), text=f"{username} has {years} years and {days} days left in the group (Chat ID: {member_chatid}) ✅")
    else:
        await bot.send_message(chat_id=int(ADMINID),  text=f"There are no active subscribers in the group")

async def membercheck():
    while True:
        await membershipwarning()
        await remove_expiredsubscribers()
        await asyncio.sleep(43200)

# TELEGRAM BOT FUNCTIONS
# add new memebre to database
async def New_Memeber(update, context):
    try:
        new_member = update.message.new_chat_members[0]
        chatid=new_member.id
        query=('SELECT * FROM subscriber WHERE "telegramId" = %s AND "botId" = %s')
        values=(str(chatid),BOTID)
        rows = await execute_query(query,values,True)
        if(len(rows)<1):
            expireTime=(datetime.utcnow() + timedelta(minutes=5))
            await bot.ban_chat_member(chat_id=GROUPCHATID, user_id=chatid,until_date=expireTime)
            await bot.ban_chat_member(chat_id=GROUPCHATID, user_id=chatid)
            await context.bot.send_message(chat_id=chatid, text="You are not eligible to join this group, You have no active subscription")
            await context.bot.send_message(chat_id=int(ADMINID), text=f"Kicked out {new_member.first_name} for joining with no subscription")
        elif (rows[0][2]==str(chatid)and rows[0][5]=="FALSE"):
            now = datetime.now()
            joinDate=now.strftime("%Y-%m-%d")
            expirydate=now+timedelta(days=int(rows[0][6]))
            duration=rows[0][6]
            final_Expirydate=expirydate.strftime("%Y-%m-%d")
            query ='UPDATE subscriber SET "joinDate" = %s, "expiryDate" = %s, "active" = %s WHERE "telegramId" = %s AND "botId" = %s'
            values=(joinDate,final_Expirydate,'TRUE',str(chatid),BOTID)
            await execute_query(query,values)
            welcome_message = f"Welcome to the group, {new_member.first_name}!\nClick /status to view how many days you have left."
            await context.bot.send_message(chat_id=chatid, text=welcome_message)
            await context.bot.send_message(chat_id=int(ADMINID), text=f"{new_member.first_name}  paid for {duration}days subscription and just Joined the group!")
    except Exception as e:
        print(e)

# manually remove user from group
async def ban(update, context):
    if update.effective_chat.id == int(ADMINID):
        if context.args:
            chatid = context.args[0]
            try:
                chatid = int(chatid)
                expireTime=(datetime.utcnow() + timedelta(minutes=5))
                await bot.ban_chat_member(chat_id=GROUPCHATID, user_id=chatid,until_date=expireTime)
                query = 'DELETE FROM subscriber WHERE "telegramId" = %s  AND "botId"=%s'
                values = (str(chatid),BOTID)
                await execute_query(query,values)
                await bot.send_message(chat_id=int(ADMINID), text=f"User {chatid} has been kicked out")
                await bot.send_message(chat_id=chatid, text="You have been kicked out from the group!")
            except ValueError:
                await bot.send_message(chat_id=update.effective_chat.id, text="Invalid chat ID provided.")
        else:
            # Handle the case where no argument is provided with the command
            await bot.send_message(chat_id=update.effective_chat.id, text="Please provide a chat ID after the command.")
async def checkallmembers(update,context):
    if (update.effective_chat.id==ADMINID):
        await remove_expiredsubscribers()
        await check_activemebers()

async def all_commands(update, context):
    if (update.effective_chat.id==int(ADMINID)):
        allcommands="/start\n/tokenstart-create token\n/ban-kickout member\n/checkallmembers-Check VIP memebers\n/status-Shows Vip status\n/startdb-restart database\n/broadcast-Broadcast message\n/help-help"
        await bot.send_message(chat_id=update.effective_chat.id,text=allcommands)


async def membershipstatus(update,context):
    query='SELECT * FROM subscriber WHERE "telegramId" = %s AND "active"=%s AND "botId" = %s'
    values=[str(update.effective_chat.id),'TRUE',BOTID]
    rows =await execute_query(query,values,True)
    if rows:
        for i in rows:
            username=i[1]
            expiry_date= datetime.strptime(i[4],'%Y-%m-%d')
            formatted_expirydate = expiry_date.strftime("%A %B %d, %Y")
            timeleft=expiry_date-datetime.now()
            timeleft=str(timeleft)
            daysleft=timeleft.split(",")
            time_days=daysleft[0].split("days")
            years = int(time_days[0]) //365
            days = int(time_days[0]) % 365
            if(years==0):
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"PIPSMATRIX INNER ⭕️\n\nTime Left:{str(days)} days\n\nYour payment is valid until:\n📅{formatted_expirydate}\n\nEnjoy your exclusive access✅")
            else:
                if (years>10):
                    years="Unlimited"
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"PIPSMATRIX INNER ⭕️\n\nTime Left:{years}\n\nYour payment is valid until:\n📅{formatted_expirydate}\n\nEnjoy your exclusive access✅")
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"PIPSMATRIX INNER ⭕️\n\nTime Left:{str(years)} years and {str(days)} days\n\nYour payment is valid until:\n📅{formatted_expirydate}\n\nEnjoy your exclusive access✅")
    else:

        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not a member of the INNER ⭕️. Clic/start 👈 to join today")

async def error(update, context):
    try:
        user_first_name = update.message.from_user.first_name
        user_chat_id = update.message.chat_id
        error_message = f"Error occurred for user {user_first_name} (Chat ID: {user_chat_id}) - Update: {update}, Error: {context.error}"
        await context.bot.send_message(chat_id=int(ADMINID), text=error_message)
    except:
        error_message = f"Error: {context.error}"
        await context.bot.send_message(chat_id=int(ADMINID), text=error_message)

async def async_user_management_tasks():
    tasks = [membercheck()]
    await asyncio.gather(*tasks)

def userManagement_main(dp,botx):
    global bot
    bot=botx
    asyncio.create_task(membercheck())
    dp.add_error_handler(error)
    dp.add_handler(CommandHandler("ban",ban))
    dp.add_handler(CommandHandler("status",membershipstatus))
    dp.add_handler(CommandHandler("allcommands",all_commands))
    dp.add_handler(CommandHandler('add_user', add_user_to_group))
    dp.add_handler(CommandHandler('checkallmembers',checkallmembers))
    dp.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,New_Memeber))

