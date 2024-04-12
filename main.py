import asyncio
import os
from dataclasses import dataclass
from dotenv import load_dotenv
import telegram as tgram
from telegram import Update
from http import HTTPStatus
from telegram.ext import ApplicationBuilder, Application, CallbackContext, ExtBot, TypeHandler, CommandHandler,ContextTypes
from telegram.constants import ParseMode
import uvicorn
from bot.broadcaster import Broadcastermain
from bot.userInterface import userInterface_main
from bot.Token import Token_main
from bot.userManagment import userManagement_main
from quart import Response, abort, request
from Update_Context import CustomContext,WebhookUpdate
from payments.banks.Paystack import paystackWebhook
from payments.crypto.binancePay import binacepayWebhook
from config.quartServer import app
from config.config_management import config_manager
load_dotenv()


context_types = ContextTypes(context=CustomContext)
dp= (
    Application.builder().token(config_manager().get_telegram_config()["telegram_apikey"]).updater(None).context_types(context_types).build()
)
@app.route("/telegram",methods=['POST'])  # type: ignore[misc]
async def telegram() -> Response:
    bot = tgram.Bot(config_manager().get_telegram_config()["telegram_apikey"])
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    #await bot.send_message(chat_id=1591573930, text="webhook received ")
    await dp.update_queue.put(
        Update.de_json(data=await request.get_json(), bot=dp.bot)
    )
    return Response(status=HTTPStatus.OK)

@app.route("/health",methods=["GET"])
async def healthcheck():
    return {"message":"Bot is running succesfully"}

@app.route("/submitpayload", methods=["GET", "POST"])  # type: ignore[misc]
async def custom_updates() -> Response:
    try:
        user_id = int(request.args["user_id"])
        payload = request.args["payload"]
    except KeyError:
        abort(
            HTTPStatus.BAD_REQUEST,
            "Please pass both `user_id` and `payload` as query parameters.",
        )
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, "The `user_id` must be a string!")

    await dp.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
    return Response(status=HTTPStatus.OK)

async def start2(update, context) -> None:
    """Display a message with instructions on how to use this bot."""
    text = ("test 2 works with no parameters")
    await update.message.reply_html(text=text)



async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(chat_id=int(os.getenv("OGB_chatid")), text=text, parse_mode=ParseMode.HTML)

async def main():
    bot = tgram.Bot(config_manager().get_telegram_config()["telegram_apikey"])
    config_manager()
    Broadcastermain(dp)
    userInterface_main(dp)
    Token_main(dp)
    userManagement_main(dp, bot)
    # Run application and webserver together
    dp.add_handler(CommandHandler("start2", start2))
    dp.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))
    port=int(os.getenv("PORT",5000))
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=app,
            port=port,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    await dp.bot.set_webhook(url=f"{os.getenv('domain')}/telegram", allowed_updates=Update.ALL_TYPES)

    async with dp:
        await dp.start()
        await webserver.serve()
        await dp.stop()
if __name__ == "__main__":
    try:
        asyncio.run(main())

    except Exception as e:
        print(e)