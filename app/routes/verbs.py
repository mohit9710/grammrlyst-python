from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import SessionLocal
from app.db.models import Verbs
from app.schemas.verbs import VerbResponse
# from core.dependencies import get_current_user  # optional

router = APIRouter(
    prefix="/verbs",
    tags=["Verbs"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ GET VERB LIST API
@router.get("/", response_model=List[VerbResponse])
def get_verbs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    # user_id: int = Depends(get_current_user)  # enable if auth needed
):
    offset = (page - 1) * limit

    verbs = (
        db.query(Verbs)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return verbs
