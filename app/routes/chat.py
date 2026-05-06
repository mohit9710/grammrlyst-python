from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.core.sentence import correct_sentence
from app.core.roleplay import get_roleplay_response
from starlette.concurrency import run_in_threadpool
from app.core.dependencies import get_current_user
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import UserDailyUsage
from app.db.purchase import Purchase, Plan

router = APIRouter(prefix="/sentence", tags=["Sentence Correction"])

# =====================================================
# 🔥 CONFIG (DAILY LIMITS)
# =====================================================
FREE_MESSAGES = 5
PAID_MESSAGES = 15

# =====================================================
# 🔌 DB DEP
# =====================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================
# --- Models ---
# =====================================================

class SentenceRequest(BaseModel):
    sentence: str = Field(..., min_length=1, max_length=500)

class RoleplayRequest(BaseModel):
    role_title: str
    user_input: str


# =====================================================
# --- Sentence Correction ---
# =====================================================

@router.post("/correct")
async def sentence_correct(req: SentenceRequest):
    try:
        result = await run_in_threadpool(correct_sentence, req.sentence)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="SERVER_ERROR")


def get_user_plan(db: Session, user_id: int):
    purchase = db.query(Purchase).filter(
        Purchase.user_id == user_id
    ).order_by(Purchase.id.desc()).first()

    if not purchase:
        return "free"

    plan = db.query(Plan).filter(
        Plan.id == purchase.plan_id
    ).first()

    if not plan:
        return "free"

    return plan.sub_name.lower()  # "basic", "pro"

# =====================================================
# --- Roleplay Chat (DAILY LIMIT - DB BASED) ---
# =====================================================
@router.post("/roleplay")
async def roleplay_chat(
    req: RoleplayRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.id
        today = date.today()

        user_plan = get_user_plan(db, user_id)

         # =====================================================
        # 🔒 DETERMINE LIMIT
        # =====================================================
        if user_plan == "pro":
            limit = float("inf")
        elif user_plan == "basic":
            limit = PAID_MESSAGES
        else:
            limit = FREE_MESSAGES

        # =====================================================
        # 🔍 GET OR CREATE TODAY USAGE
        # =====================================================
        usage = db.query(UserDailyUsage).filter(
            UserDailyUsage.user_id == user_id,
            UserDailyUsage.usage_date == today
        ).first()

        if not usage:
            usage = UserDailyUsage(
                user_id=user_id,
                usage_date=today,
                message_count=0
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)

        # =====================================================
        # 🚫 CHECK LIMIT
        # =====================================================
        if usage.message_count >= limit:
            raise HTTPException(
                status_code=403,
                detail="DAILY_LIMIT_REACHED"
            )

        # =====================================================
        # 🤖 AI RESPONSE
        # =====================================================
        result = await run_in_threadpool(
            get_roleplay_response,
            req.role_title,
            req.user_input
        )

        # =====================================================
        # 📈 UPDATE USAGE
        # =====================================================
        usage.message_count += 1
        usage.last_message_at = datetime.utcnow()
        db.commit()

        # =====================================================
        # 📤 RESPONSE
        # =====================================================
        return {
            **result,
            "usage": {
                "used": usage.message_count,
                "limit": "unlimited" if limit == float("inf") else limit,
                "remaining": (
                    "unlimited"
                    if limit == float("inf")
                    else max(0, limit - usage.message_count)
                )
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SERVER_ERROR"
        )