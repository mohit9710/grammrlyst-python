from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db.session import SessionLocal
from app.db.models import PronunciationText
from app.schemas.pronounciation import TextResponse
from sqlalchemy import func

router = APIRouter(
    prefix="/practice",
    tags=["Pronounciation"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ GET QUIZ BY LESSON ID
@router.get("/pronounciation", response_model=TextResponse)
def get_random_text(difficulty: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PronunciationText)
    
    if difficulty:
        query = query.filter(PronunciationText.difficulty_level == difficulty)
    
    text = query.order_by(func.rand()).first()
    
    if not text:
        raise HTTPException(status_code=404, detail="No texts found")
    return text