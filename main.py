import asyncio
import os
from dotenv import load_dotenv
import telegram as tgram
from telegram import Update
from http import HTTPStatus
from telegram.ext import  Application, TypeHandler,ContextTypes
from telegram.constants import ParseMode
import uvicorn
from Update_Context import CustomContext,WebhookUpdate,webhook_update
from bot.broadcaster import Broadcastermain
from bot.userInterface import userInterface_main
from bot.Token import Token_main
from bot.userManagment import userManagement_main
from quart import Response, abort, request
from config.config_management import config_manager
if config_manager().get_paystack_config():
    from payments.banks.Paystack import paystackWebhook
    
if config_manager().get_binance_config():
    from payments.crypto.binancePay import binacepayWebhook

if config_manager().get_stripe_config():
    from payments.banks.Stripe import stripeWebhook

if config_manager().get_coinpayment_config():
    from payments.crypto.coinPayments import coinpaymentwebhook
if config_manager().get_nowpayment_config():
    from payments.crypto.nowPayments import nowpayments_webhook
    
from config.quartServer import app

load_dotenv()

async def main():
    context_types = ContextTypes(context=CustomContext)
    dp= (
    Application.builder().token(config_manager().get_telegram_config()["telegram_apikey"]).updater(None).context_types(context_types).build())
    
    @app.route("/health",methods=["GET"])
    async def healthcheck():
        return {"message":"Bot is running succesfully"}


    @app.route("/telegram",methods=['POST'])
    async def telegram() -> Response:
        bot = tgram.Bot(config_manager().get_telegram_config()["telegram_apikey"])
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await dp.update_queue.put(
            Update.de_json(data=await request.get_json(), bot=dp.bot)
        )
        return Response(status=HTTPStatus.OK)
    
    @app.route("/submitpayload", methods=["GET", "POST"])
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

    bot = tgram.Bot(config_manager().get_telegram_config()["telegram_apikey"])
    config_manager()
    Broadcastermain(dp)
    userInterface_main(dp)
    Token_main(dp)
    userManagement_main(dp, bot)

 
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
        await bot.send_message(chat_id=int(config_manager().get_metadata_config()["adminId"]), text=f'Bot deployed succefully click /start to check it out')
        await webserver.serve()
        await dp.stop()
if __name__ == "__main__":
    try:
        asyncio.run(main())

    except Exception as e:
        print(e)