from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import SessionLocal
from app.db.models import User
from app.schemas.auth import SignUpSchema, SignInSchema
from app.core.security import hash_password, verify_password, create_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(payload: SignUpSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=payload.email,
        password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}

@router.post("/signin")
def signin(payload: SignInSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(
        {"user_id": user.id},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_token(
        {"user_id": user.id},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
