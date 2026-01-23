from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db.session import SessionLocal
from app.db.models import Sentence, SpellingChallenge, ScrambleChallenge # Import both
from app.schemas.sentence import SentenceSchema, SpellingSchema, ScrambleSchema # Import both

router = APIRouter(
    prefix="/games",
    tags=["Games"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/sentences", response_model=List[SentenceSchema])
def get_random_sentences(
    limit: int = Query(5, gt=0, le=20), 
    db: Session = Depends(get_db)
):
    """
    Fetches a random set of sentences for the game.
    """
    sentences = db.query(Sentence).order_by(func.rand()).limit(limit).all()
    return sentences

@router.get("/sentences/difficulty/{level}", response_model=List[SentenceSchema])
def get_sentences_by_difficulty(
    level: str, 
    limit: int = Query(5, gt=0, le=20), 
    db: Session = Depends(get_db)
):
    """
    Fetches random sentences based on a specific difficulty level (easy, medium, hard).
    """
    sentences = (
        db.query(Sentence)
        .filter(Sentence.difficulty == level)
        .order_by(func.rand())
        .limit(limit)
        .all()
    )
    
    if not sentences:
        raise HTTPException(status_code=404, detail=f"No sentences found for difficulty: {level}")
    
    return sentences

# --- New Spelling Endpoint ---
@router.get("/spelling/", response_model=List[SpellingSchema])
def get_random_spelling_words(limit: int = Query(10, gt=0), db: Session = Depends(get_db)):
    """
    Fetches random misspelled/correct word pairs for the spelling game.
    """
    words = db.query(SpellingChallenge).order_by(func.rand()).limit(limit).all()
    
    if not words:
        raise HTTPException(status_code=404, detail="No spelling data found in database")
        
    return words

@router.get("/scramble", response_model=List[ScrambleSchema])
def get_scramble_game(limit: int = 5, db: Session = Depends(get_db)):
    """Fetches random word scramble challenges."""
    return db.query(ScrambleChallenge).order_by(func.rand()).limit(limit).all()