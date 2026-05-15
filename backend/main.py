import secrets

import stripe
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from database import get_by_api_key, init_db, create_subscription, update_status
from services.analyze import analyze_contract
from services.extract_pdf import extract_text as extract_pdf_text
from services.stripe_service import construct_webhook_event, create_checkout_session
from services.email_service import send_api_key_email

app = FastAPI(title="Cautelio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── Auth dependency ──────────────────────────────────────────────────────────

async def require_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required.")
    row = get_by_api_key(x_api_key)
    if not row or row["status"] != "active":
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")
    return row


# ── Payment ──────────────────────────────────────────────────────────────────

@app.get("/checkout")
def checkout():
    url = create_checkout_session()
    return RedirectResponse(url)


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = construct_webhook_event(payload, sig)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook.")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session["customer"]
        subscription_id = session["subscription"]
        email = session["customer_details"]["email"]

        api_key = "caut_" + secrets.token_urlsafe(32)
        create_subscription(api_key, customer_id, subscription_id, email)
        send_api_key_email(email, api_key)

    elif event["type"] in (
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ):
        sub = event["data"]["object"]
        update_status(sub["id"], "cancelled")

    elif event["type"] == "customer.subscription.resumed":
        sub = event["data"]["object"]
        update_status(sub["id"], "active")

    return {"ok": True}


# ── Key validation (used by extension on setup) ───────────────────────────────

@app.get("/validate-key")
async def validate_key(sub=Depends(require_key)):
    return {"ok": True, "email": sub["email"]}


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str
    freelancer_mode: bool = False


@app.post("/analyze")
async def analyze(req: AnalyzeRequest, _=Depends(require_key)):
    if len(req.text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Contract text too short.")
    try:
        return await analyze_contract(req.text, req.freelancer_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    freelancer_mode: str = Form("false"),
    _=Depends(require_key),
):
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
