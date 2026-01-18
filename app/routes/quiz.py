from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.session import SessionLocal
from app.db.models import QuizQuestion
from app.schemas.quiz import QuizQuestionResponse

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ GET QUIZ BY LESSON ID
@router.get("/{lesson_id}", response_model=List[QuizQuestionResponse])
def get_quiz_by_lesson(
    lesson_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    # Using joinedload to fetch options in a single query (optimization)
    questions = (
        db.query(QuizQuestion)
        .options(joinedload(QuizQuestion.options))
        .filter(QuizQuestion.lesson_id == lesson_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this lesson")

    return questions