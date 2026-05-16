import logging
import os

import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import (activate_user, create_user, deactivate_user, get_user_by_email,
                      get_user_by_key, init_db)
from services.analyze import analyze_contract
from services.email import send_welcome_email
from services.extract_pdf import extract_text as extract_pdf_text

init_db()

app = FastAPI(title="Cautelio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Auth ─────────────────────────────────────────────────────────────────────

def require_user(api_key: str):
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Get yours at cautelioai.xyz")
    user = get_user_by_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    if user["status"] != "active" or user["plan"] != "paid":
        raise HTTPException(status_code=403, detail="No active subscription. Visit cautelioai.xyz to subscribe.")
    return user


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Key validation ────────────────────────────────────────────────────────────

@app.get("/validate-key")
def validate_key(x_api_key: str = Header(...)):
    user = require_user(x_api_key)
    return {"ok": True, "email": user["email"]}


# ── Payment ───────────────────────────────────────────────────────────────────

@app.get("/checkout")
def checkout():
    session = stripe.checkout.Session.create(
        api_key=os.environ["STRIPE_SECRET_KEY"],
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": os.environ["STRIPE_PRICE_ID"], "quantity": 1}],
        success_url=f"{os.environ['FRONTEND_URL']}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.environ['FRONTEND_URL']}/cancel.html",
    )
    return RedirectResponse(session.url)


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature.")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = (session.get("customer_details") or {}).get("email")
        if email:
            existing = get_user_by_email(email)
            if not existing:
                create_user(email)
            activate_user(email)
            user = get_user_by_email(email)
            sent = send_welcome_email(email, user["api_key"])
            logger.info("Activated user: %s | email sent: %s", email, sent)

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        session = event["data"]["object"]
        # Look up by customer ID
        customer = stripe.Customer.retrieve(
            session["customer"],
            api_key=os.environ["STRIPE_SECRET_KEY"]
        )
        email = customer.get("email")
        if email:
            deactivate_user(email)
            logger.info("Deactivated user: %s", email)

    return JSONResponse({"status": "ok"})


# ── Analysis ──────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(
    text: str = Form(...),
    freelancer_mode: str = Form("false"),
    x_api_key: str = Header(...),
):
    require_user(x_api_key)
    if len(text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Contract text too short.")
    try:
        return await analyze_contract(text, freelancer_mode.lower() == "true")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    freelancer_mode: str = Form("false"),
    x_api_key: str = Header(...),
):
    require_user(x_api_key)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    try:
        pdf_bytes = await file.read()
        text = extract_pdf_text(pdf_bytes)
        if len(text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Could not extract enough text from this PDF.")
        return await analyze_contract(text[:40000], freelancer_mode.lower() == "true")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
