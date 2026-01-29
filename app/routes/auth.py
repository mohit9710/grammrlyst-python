from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models import User
from app.db.models import Verbs
from app.schemas.auth import SignUpSchema, SignInSchema, ResetPasswordSchema, ForgotPasswordSchema
from app.core.security import hash_password, verify_password, create_token, generate_email_token, generate_reset_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.dependencies import get_current_user
from app.core.mail import send_verification_email, send_reset_password_email

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

    if len(payload.password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    token = generate_email_token()

    user = User(
        # name=payload.first_name+" "+payload.last_name,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password=hash_password(payload.password),
        email_verification_token=token,
        is_email_verified=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_token(
        {"user_id": user.id},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_token(
        {"user_id": user.id},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    send_verification_email(user.email, token)

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/signin")
def signin(payload: SignInSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first"
        )

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

@router.get("/userprofile")
def get_profile(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.first_name,
        "email": user.email,
    }

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email_verification_token == token
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.is_email_verified = True
    user.email_verification_token = None

    db.commit()

    return {
        "message": "Email verified successfully 🎉"
    }

@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordSchema,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    token = generate_reset_token()

    user.reset_password_token = token
    user.reset_password_expires = datetime.utcnow() + timedelta(minutes=15)

    db.commit()

    send_reset_password_email(user.email, token)

    return {
        "message": "If the email exists, a reset link has been sent"
    }

@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordSchema,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.reset_password_token == payload.token
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if user.reset_password_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user.password = hash_password(payload.new_password)
    user.reset_password_token = None
    user.reset_password_expires = None

    db.commit()

    return {
        "message": "Password reset successfully"
    }