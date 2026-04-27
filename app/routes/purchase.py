from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user_id
from app.schemas.auth import PurchaseSchema
from app.db.referral import Referral, ReferralStatus, ReferralType
from app.db.models import InstituteEarning
from datetime import datetime, timedelta

router = APIRouter(prefix="/purchase", tags=["Purchase"])


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