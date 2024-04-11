API_key ="sk_test_51OBxysCFLuGCoy5bsn3FDabxe7njlEoIjtzNkn2rIn0snLtsa6l0so0HleK3irojdbO0rnKBUkV2GjIpzonFMFFG00RjLSQSsP"
import stripe

# Set your Stripe secret key
stripe.api_key =API_key

def create_checkout_session(amount, currency='usd'):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': 'Your Product Name',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        return session.id
    except stripe.error.StripeError as e:
        return str(e)

if __name__ == "__main__":
    # Set the payment amount in cents
    payment_amount = 1000  # $10.00

    session_id = create_checkout_session(payment_amount)

    if "Error:" in session_id:
        print(f"Error creating Checkout Session: {session_id}")
    else:
        checkout_url = f"https://checkout.stripe.com/{session_id}"
        print(f"Checkout URL: {checkout_url}")
