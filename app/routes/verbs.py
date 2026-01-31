from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import SessionLocal
from app.db.models import Verbs, UserVerbProgress,User
from app.schemas.verbs import VerbResponse, VerbViewSchema
from app.core.dependencies import get_current_user
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt

router = APIRouter(
    prefix="/verbs",
    tags=["Verbs"]
)

# -------------------------
# Database Session
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Optional Auth Dependency
# -------------------------
# -------------------------
# Optional Auth Dependency
# -------------------------
def get_current_user_optional(
    authorization: str = Header(None), 
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None
# =====================================================
# GET VERB LIST WITH OPTIONAL USER PROGRESS
# =====================================================
@router.get("/", response_model=List[VerbResponse])
def list_verbs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user_optional) 
):
    offset = (page - 1) * limit
    verbs = db.query(Verbs).offset(offset).limit(limit).all()
    
    response = []
    for v in verbs:
        # Convert SQLAlchemy model to a dictionary
        verb_data = {
            "id": v.id,
            "base": v.base,
            "past": v.past,
            "past_participle": v.past_participle,
            "meaning": v.meaning,
            "example": v.example,
            "type": v.type,
            "progress": None  # Default to None
        }

        # If user is logged in, find their specific progress for THIS verb
        if user:
            p = db.query(UserVerbProgress).filter_by(user_id=user.id, verb_id=v.id).first()
            if p:
                verb_data["progress"] = {
                    "views": p.views, 
                    "stage": p.stage
                }
        
        response.append(verb_data)

    return response



# =====================================================
# MARK VERB AS VIEWED (PRIVATE)
# =====================================================
@router.post("/view")
def mark_verb_viewed(
    data: VerbViewSchema,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = (
        db.query(UserVerbProgress)
        .filter_by(user_id=user.id, verb_id=data.verb_id)
        .first()
    )

    now = datetime.utcnow()

    if not progress:
        # First time viewing this verb
        progress = UserVerbProgress(
            user_id=user.id,
            verb_id=data.verb_id,
            views=1,
            stage=1,
            first_view=now,
            last_view=now
        )
        db.add(progress)
    else:
        # Increment views and update stage
        progress.views += 1
        progress.last_view = now

        progress.stage = (
            3 if progress.views >= 5
            else 2 if progress.views >= 3
            else 1
        )

    db.commit()

    return {
        "message": "Verb progress updated",
        "views": progress.views,
        "stage": progress.stage
    }
