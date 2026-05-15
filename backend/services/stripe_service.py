import os
import stripe

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]


def create_checkout_session() -> str:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": os.environ["STRIPE_PRICE_ID"], "quantity": 1}],
        success_url=f"{os.environ['FRONTEND_URL']}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.environ['FRONTEND_URL']}/cancel.html",
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(
        payload, sig_header, os.environ["STRIPE_WEBHOOK_SECRET"]
    )
