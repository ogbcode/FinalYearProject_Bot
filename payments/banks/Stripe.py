import asyncio
import os
import string
from quart import Quart, jsonify, request
import stripe
import stripe.webhook
from urllib3 import HTTPResponse
from bot.userManagment import add_transaction, add_user_to_group, convert_country_code
from config.quartServer import app


from config.config_management import config_manager
stripe.api_key =config_manager().get_stripe_config()["stripe_apikey"]

metadata=config_manager().get_metadata_config()

def set_webhook(url):
    try:
        webhook=stripe.WebhookEndpoint.create(
            enabled_events= ['charge.succeeded', 'charge.failed'],
            url=url
        )
        return(webhook.secret)
    except stripe.error.StripeError as e:
        print("Error creating webhook endpoint:", e)
# set_webhook(f"{os.getenv('domain')}/stripe")
def verify_stripe_webhook(body,signature):
  endpoint_secret=config_manager().get_stripe_config()["stripe_secret"]
  payload = body
  sig_header = signature
  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
    return True
  except Exception as e:
    print(e)
    return False

async def create_stripe_checkout(telegramId,duration,amount):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card','cashapp'],
            line_items=[{
                'price_data': {
                    'currency':'usd',
                    'product_data': {
                        'name':metadata['name'],
                    },
                    'unit_amount': int(amount)*100,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=metadata['success_url'],
            metadata={"duration":str(duration),"telegramId":str(telegramId)}
        )
        return session.url
    except stripe.error.StripeError as e:
        print (e)
processedPayments=set()

@app.route('/stripe', methods=['POST'])
async def stripeWebhook():
    try:
        event_data = await request.get_json()
        transactid=event_data["id"]
        if transactid in processedPayments:
            return jsonify({"message": "Payment already processed"}), 200
        signature = request.headers.get('Stripe-Signature')
        body=await  request.get_data(as_text=True)
        if not verify_stripe_webhook(body,signature):
            return jsonify({"message": "Bad Request"}), 400

        payment_status = event_data.get("data", {}).get("object", {}).get("payment_status")


        if payment_status == 'paid':
            processedPayments.add(transactid)
            transaction_id = event_data.get("data", {}).get("object", {}).get("id")
            amount = event_data.get("data", {}).get("object", {}).get("amount_total") / 100
            firstName = event_data.get("data", {}).get("object", {}).get("customer_details", {}).get("name")
            telegramId = event_data.get("data", {}).get("object", {}).get("metadata", {}).get("telegramId")
            duration = event_data.get("data", {}).get("object", {}).get("metadata", {}).get("duration")
            country = event_data.get("data", {}).get("object", {}).get("customer_details", {}).get("address", {}).get("country")

            await add_transaction(transaction_id,"SUCCESS",str(amount),"USD","Stripe",duration,telegramId,convert_country_code(country))
            await add_user_to_group(user_id=telegramId,first_name=firstName,duration=duration)
           
            return jsonify({"message": "Verification Succes"}), 200
        
        return jsonify({"message": "Verification failed"}), 400


    except Exception as e:
        print(e) 
        return jsonify({"error": "Internal server Error"}), 500
  

 
