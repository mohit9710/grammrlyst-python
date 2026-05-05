from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user_id, require_active_plan
from app.schemas.auth import PurchaseSchema
from app.schemas.purchase import PurchaseVerifySchema
from app.db.referral import Referral, ReferralStatus, ReferralType
from app.db.models import InstituteEarning
from app.db.models import InstituteEarning
from app.db.purchase import Purchase
from datetime import datetime, timedelta
import requests, os
import pytz
import hmac
import hashlib

router = APIRouter(prefix="/purchase", tags=["Purchase"])

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_commission_percent(total_referrals: int):
    if total_referrals >= 200:
        return 30
    elif total_referrals >= 50:
        return 20
    return 10


@router.post("/transit")
def purchase(
    payload: PurchaseSchema,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    amount = payload.amount  # ✅ FIX 1

    # 🔹 Find referral (ONLY completed ones)
    referral = db.query(Referral).filter(
        Referral.referee_id == current_user_id,  # ✅ FIX 2
        Referral.referral_type == ReferralType.institute,
    ).first()

    # 👉 No referral → normal purchase
    if not referral:
        return {"message": "Purchase successful (no commission)"}

    institute_id = referral.referrer_id

    # 🔹 Count completed referrals
    total_referrals = db.query(Referral).filter(
        Referral.referrer_id == institute_id,
        Referral.referral_type == ReferralType.institute,
        Referral.status == ReferralStatus.completed
    ).count()

    percent = get_commission_percent(total_referrals)

    commission_amount = (amount * percent) / 100

    # ❌ Prevent duplicate earnings
    existing = db.query(InstituteEarning).filter(
        InstituteEarning.referred_user_id == current_user_id
    ).first()

    if existing:
        return {"message": "Purchase already recorded"}

    # 🔹 Save earning
    earning = InstituteEarning(
        institute_user_id=institute_id,
        referred_user_id=current_user_id,
        base_amount=amount,
        commission_percent=percent,
        commission_amount=commission_amount,
        status="pending"
    )

    db.add(earning)


    referral.status = ReferralStatus.completed
    referral.completed_at = datetime.utcnow()
    db.add(referral)
    db.commit()

    return {
        "message": "Purchase successful",
        "commission": commission_amount,
        "percent": percent
    }

def capture_payment(payment_id: str, amount: float):
    try:
        if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
            raise Exception("Razorpay keys missing")

        # ✅ convert to paise (integer)
        amount_paise = int(float(amount) * 100)

        url = f"https://api.razorpay.com/v1/payments/{payment_id}/capture"

        data = {
            "amount": amount_paise,
            "currency": "INR"
        }

        response = requests.post(
            url,
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json=data
        )

        # 🔥 DEBUG (VERY IMPORTANT)
        print("Capture Status:", response.status_code)
        print("Capture Response:", response.text)

        return response.json()

    except Exception as e:
        print("CAPTURE ERROR:", str(e))
        return {"error": str(e)}

def create_qr_payment(user_id: int, amount: float, plan: str):
    try:
        if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
            raise Exception("Razorpay keys missing")

        ist = pytz.timezone("Asia/Kolkata")
        close_by_time = datetime.now(ist) + timedelta(minutes=10)

        # ✅ force integer paise
        amount_paise = int(float(amount) * 100)

        url = "https://api.razorpay.com/v1/payments/qr_codes"

        data = {
            "type": "upi_qr",
            "name": f"user_{user_id}",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": plan,
            "close_by": int(close_by_time.timestamp()),
            "notes": {
                "user_id": str(user_id),
                "plan": plan
            }
        }

        response = requests.post(
            url,
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json=data
        )
        # 🔥 DEBUG (VERY IMPORTANT)
        print("Razorpay Status:", response.status_code)
        print("Razorpay Response:", response.text)

        return response.json()

    except Exception as e:
        print("QR ERROR:", str(e))
        return {"error": str(e)}


def check_qr_payment(qr_id: str):
    url = f"https://api.razorpay.com/v1/payments/qr_codes/{qr_id}/payments"

    response = requests.get(
        url,
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )

    return response.json()

@router.post("/start")
def start_payment(
    payload: PurchaseSchema,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    if not payload.amount or not payload.plan_name:
        raise HTTPException(status_code=400, detail="Invalid payload")

    qr = create_qr_payment(
        user_id=current_user_id,
        amount=payload.amount,
        plan=payload.plan_name
    )

    # ✅ Razorpay returned error
    if "error" in qr:
        raise HTTPException(
            status_code=400,
            detail=qr["error"]
        )

    # ❌ Invalid response
    if "image_url" not in qr:
        raise HTTPException(
            status_code=400,
            detail=f"QR failed: {qr}"
        )

    return {
        "qr_id": qr["id"],
        "qr_image": qr["image_url"]
    }


@router.post("/status")
def check_and_complete_payment(
    qr_id: str,
    payload: PurchaseSchema,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    payment_data = check_qr_payment(qr_id)

    if payment_data.get("count", 0) == 0:
        return {"status": "pending"}

    payment = payment_data["items"][0]

    # ✅ Payment confirmed → NOW call transit logic

    amount = payload.amount

    referral = db.query(Referral).filter(
        Referral.referee_id == current_user_id,
        Referral.referral_type == ReferralType.institute,
    ).first()

    if not referral:
        return {"status": "success", "message": "No commission"}

    institute_id = referral.referrer_id

    total_referrals = db.query(Referral).filter(
        Referral.referrer_id == institute_id,
        Referral.referral_type == ReferralType.institute,
        Referral.status == ReferralStatus.completed
    ).count()

    percent = get_commission_percent(total_referrals)
    commission_amount = (amount * percent) / 100

    existing = db.query(InstituteEarning).filter(
        InstituteEarning.referred_user_id == current_user_id
    ).first()

    if not existing:
        earning = InstituteEarning(
            institute_user_id=institute_id,
            referred_user_id=current_user_id,
            base_amount=amount,
            commission_percent=percent,
            commission_amount=commission_amount,
            status="completed"
        )

        db.add(earning)

        referral.status = ReferralStatus.completed
        referral.completed_at = datetime.utcnow()

        db.commit()

    return {
        "status": "success",
        "payment_id": payment.get("id"),
        "commission": commission_amount
    }

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    data = await request.json()

    event = data.get("event")

    # ✅ only handle successful payments
    if event == "payment.captured":
        payment = data["payload"]["payment"]["entity"]

        payment_id = payment["id"]
        amount = payment["amount"]
        currency = payment["currency"]
        status = payment["status"]
        method = payment["method"]

        notes = payment.get("notes", {})
        user_id = int(notes.get("user_id"))

        # ✅ check duplicate
        existing = db.query(Transaction).filter(
            Transaction.payment_id == payment_id
        ).first()

        if existing:
            return {"status": "already processed"}

        # ✅ save transaction
        txn = Transaction(
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status=status,
            method=method
        )
        db.add(txn)

        # ✅ update user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_paid = True

        db.commit()

        return {"status": "success"}

    return {"status": "ignored"}

@router.post("/verify")
def verify_payment(
    payload: PurchaseVerifySchema,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # ✅ Step 1: Verify signature
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"

    generated_signature = hmac.new(
        bytes(RAZORPAY_SECRET, 'utf-8'),
        bytes(body, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    if generated_signature != payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # ✅ Step 2: Get plan
    plan = db.query(Plan).filter(Plan.name == payload.plan_name).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # ✅ Step 3: Calculate access
    start_date = datetime.utcnow()

    if plan.duration_days:
        end_date = start_date + timedelta(days=plan.duration_days)
    else:
        end_date = None  # lifetime

    # ✅ Step 4: Save purchase
    purchase = Purchase(
        user_id=user_id,
        plan_id=plan.id,
        payment_id=payload.razorpay_payment_id,
        order_id=payload.razorpay_order_id,
        signature=payload.razorpay_signature,
        status="success",
        start_date=start_date,
        end_date=end_date
    )

    db.add(purchase)

    # ✅ Step 5: Update user access (optional shortcut)
    user = db.query(User).filter(User.id == user_id).first()
    user.is_paid = True

    db.commit()

    return {
        "message": "Payment verified & access granted",
        "plan": plan.name,
        "valid_till": end_date
    }

@router.get("/premium-feature")
def premium_api(purchase = Depends(require_active_plan)):
    return {
        "data": "premium content",
        "plan": purchase.plan_id,
        "plan_name": purchase.plan.name
    }

@router.get("/my-plan")
def my_plan(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    purchase = get_user_active_plan(user_id, db)

    if not purchase:
        return {"plan": "free", "active": False}

    return {
        "plan": purchase.plan.name,
        "active": True,
        "valid_till": purchase.end_date
    }

def get_user_active_plan(user_id: int, db: Session):
    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == user_id,
            Purchase.status == "success"
        )
        .order_by(Purchase.created_at.desc())
        .first()
    )

    if not purchase:
        return None

    # Lifetime plan
    if purchase.end_date is None:
        return purchase

    # Active plan
    if purchase.end_date > datetime.utcnow():
        return purchase

    return None