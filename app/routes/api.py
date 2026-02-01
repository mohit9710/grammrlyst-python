from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from app.db.session import SessionLocal
# UserActivityLog ko import karna zaroori hai
from app.db.models import DailyTip, User, UserActivityLog 
from app.core.dependencies import get_current_user
# Schema import karein (redefine karne ki zaroorat nahi)
from app.schemas.auth import XPUpdateRequest
from sqlalchemy import and_, func

router = APIRouter(
    prefix="/api",
    tags=["API Operations"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function for logging
def create_log(db: Session, user_id: int, act_type: str, desc: str, points: int = 0):
    new_log = UserActivityLog(
        user_id=user_id,
        activity_type=act_type,
        description=desc,
        points_earned=points,
        created_at=datetime.utcnow()
    )
    db.add(new_log)

# --- TIP OF THE DAY ---
@router.get("/tips/today")
def get_tip_of_the_day(db: Session = Depends(get_db)):
    tips = db.query(DailyTip).filter(DailyTip.is_active == True).all()
    if not tips:
        return {"message": "No tips available"}

    today_index = date.today().day % len(tips)
    tip = tips[today_index]

    return {
        "id": tip.id,
        "wrong": tip.wrong_sentence,
        "correct": tip.correct_sentence,
        "explanation": tip.explanation,
        "level": tip.level
    }

# --- UPDATE XP & BONUS (FastAPI) ---
# --- UPDATE XP & BONUS ---
@router.post("/update-xp")
async def update_user_stats(
    request: XPUpdateRequest,
    game_name: str = "Language Challenge",
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # db.merge zaroori hai taaki current_user session se attach ho jaye
    user = db.merge(current_user)
    today = date.today()
    
    if request.is_bonus:
        # 1. Database Check: Kya aaj ke din is user ka 'BONUS_CLAIM' log exist karta hai?
        existing_bonus = db.query(UserActivityLog).filter(
            UserActivityLog.user_id == user.id,
            UserActivityLog.activity_type == "BONUS_CLAIM",
            func.date(UserActivityLog.created_at) == today
        ).first()

        # 2. Agar bonus mil chuka hai, toh error bhej dein (Frontend display ke liye)
        if existing_bonus:
            raise HTTPException(
                status_code=400, 
                detail="Daily arcade bonus already claimed for today."
            )

        # 3. Agar nahi mila, toh User model update karein aur log create karein
        user.bonus += request.points_to_add
        create_log(db, user.id, "BONUS_CLAIM", f"Daily Arcade Entry Bonus", request.points_to_add)
        
    else:
        # Normal Game XP Logic
        user.total_xp += request.points_to_add
        user.points += (request.points_to_add // 10)
        create_log(db, user.id, "GAME_WIN", f"Won {request.points_to_add} XP in {game_name}", request.points_to_add)

    db.commit()
    db.refresh(user) # User ki updated states (total_xp, bonus) fetch karein
    
    return {
        "message": "Success", 
        "total_xp": user.total_xp, 
        "bonus": user.bonus,
        "is_awarded": True if request.is_bonus else False
    }

# --- STREAK & ACTIVITY ---
@router.post("/update-activity")
async def update_activity(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    user = db.merge(current_user)
    today = date.today()
    last_login = user.last_login_date

    if isinstance(last_login, datetime):
        last_login = last_login.date()

    if last_login is None:
        user.streak = 1
        create_log(db, user.id, "STREAK_UP", "Started a new learning streak! 🔥")
    elif last_login == today:
        pass 
    elif last_login == today - timedelta(days=1):
        user.streak += 1
        # Log sirf streak badhne par
        create_log(db, user.id, "STREAK_UP", f"Streak increased to {user.streak} days! 🔥")
    else:
        user.streak = 1 
        create_log(db, user.id, "STREAK_UP", "Streak reset! Let's start again. 💪")

    user.last_login_date = today
    db.commit()
    db.refresh(user)
    return {"streak": user.streak}

# --- FETCH RECENT LOGS ---
@router.get("/user/activity-logs")
async def get_activity_logs(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logs = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == current_user.id
    ).order_by(UserActivityLog.created_at.desc()).limit(20).all()
    
    return logs