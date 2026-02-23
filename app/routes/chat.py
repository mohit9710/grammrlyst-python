from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.core.sentence import correct_sentence
from app.core.roleplay import get_roleplay_response
from starlette.concurrency import run_in_threadpool
from app.core.dependencies import get_current_user
from datetime import date

router = APIRouter(prefix="/sentence", tags=["Sentence Correction"])

# =====================================================
# 🔥 CONFIG
# =====================================================
MAX_MESSAGES = 10          # session ends at 10 chats
FREE_DAILY_LIMIT = 1       # free user once per day

# =====================================================
# 🔥 TEMP STORAGE (⚠️ replace with Redis/DB in prod)
# =====================================================
user_daily_usage = {}      # {user_id: date}
session_message_count = {} # {session_id: count}


# =====================================================
# --- Models ---
# =====================================================

class SentenceRequest(BaseModel):
    sentence: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        example="He go to school yesterday."
    )

class SentenceResponse(BaseModel):
    original: str
    fixed: str
    rule: str = "Grammar & Style"

class RoleplayRequest(BaseModel):
    role_title: str
    user_input: str
    session_id: str


# =====================================================
# --- Sentence Correction ---
# =====================================================

@router.post("/correct")
async def sentence_correct(req: SentenceRequest):
    try:
        result = await run_in_threadpool(correct_sentence, req.sentence)
        return result

    except Exception as e:
        print(f"Route Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Server was unable to process the request."
        )


# =====================================================
# --- Roleplay Chat ---
# =====================================================

@router.post("/roleplay")
async def roleplay_chat(
    req: RoleplayRequest,
    current_user = Depends(get_current_user)
):
    """
    Roleplay chat rules:
    ✅ Free user → 1 session/day
    ✅ All users → max 10 messages/session
    """
    try:
        user_id = current_user.id
        today = date.today()
        session_id = req.session_id

        # =====================================
        # 🔥 FREE USER DAILY LIMIT (FIXED)
        # =====================================
        if not current_user.is_paid:
            last_used = user_daily_usage.get(user_id)

            # block only if new session same day
            if last_used == today and session_id not in session_message_count:
                raise HTTPException(
                    status_code=403,
                    detail="Free daily limit reached. Upgrade to continue."
                )

        # =====================================
        # 🔥 SESSION MESSAGE LIMIT
        # =====================================
        if session_id not in session_message_count:
            session_message_count[session_id] = 0

        if session_message_count[session_id] >= MAX_MESSAGES:
            raise HTTPException(
                status_code=403,
                detail="Roleplay session ended. Start a new session."
            )

        # =====================================
        # 🤖 AI RESPONSE
        # =====================================
        result = await run_in_threadpool(
            get_roleplay_response,
            req.role_title,
            req.user_input
        )

        # increment counter
        session_message_count[session_id] += 1

        # mark free usage (only first time)
        if not current_user.is_paid:
            user_daily_usage[user_id] = today

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Roleplay Route Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI tutor is currently unavailable."
        )