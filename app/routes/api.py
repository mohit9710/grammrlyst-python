from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.session import SessionLocal
from app.db.models import DailyTip
from datetime import date

router = APIRouter(
    prefix="/api",
    tags=["Daily Tips"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/tips/today")
def get_tip_of_the_day(db: Session = Depends(get_db)):
    tips = db.query(DailyTip).filter(DailyTip.is_active == True).all()

    if not tips:
        return {"message": "No tips available"}

    today = date.today().day
    index = today % len(tips)
    tip = tips[index]

    return {
        "id": tip.id,
        "wrong": tip.wrong_sentence,
        "correct": tip.correct_sentence,
        "explanation": tip.explanation,
        "level": tip.level
    }