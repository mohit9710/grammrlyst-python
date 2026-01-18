from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import SessionLocal
from app.db.models import GrammarTopic, GrammarLesson
from app.schemas.grammar import TopicResponse, LessonResponse

router = APIRouter(
    prefix="/grammar",
    tags=["Grammar"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ GET ALL TOPICS (Sidebar list)
@router.get("/topics", response_model=List[TopicResponse])
def get_topics(
    db: Session = Depends(get_db)
):
    # Usually, topics are a fixed set, so we fetch all ordered by display_order
    return db.query(GrammarTopic).order_by(GrammarTopic.display_order).all()

# ✅ GET LESSONS BY TOPIC ID
@router.get("/lessons/{topic_id}", response_model=List[LessonResponse])
def get_lessons(
    topic_id: int,
    db: Session = Depends(get_db)
):
    lessons = db.query(GrammarLesson).filter(GrammarLesson.topic_id == topic_id).all()
    if not lessons:
        raise HTTPException(status_code=404, detail="No lessons found for this topic")
    return lessons