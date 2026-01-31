from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models import User
from app.db.models import Verbs
from app.schemas.auth import SignUpSchema, SignInSchema, ResetPasswordSchema, ForgotPasswordSchema
from app.core.security import hash_password, verify_password, create_token, generate_email_token, generate_reset_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.dependencies import get_current_user, get_current_user_id
from app.core.mail import send_verification_email, send_reset_password_email
import uuid, os

router = APIRouter(prefix="/auth", tags=["Authentication"])

UPLOAD_DIR = "media/profile"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

    token = generate_email_token()
    # print(payload)
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
    # current_user is now the actual User object from your updated dependency
    current_user: User = Depends(get_current_user)
):
    # No need to query the DB here anymore! 
    # get_current_user already did the work.
    base_url = "http://127.0.0.1:8000"

    # Build the full URL only if an image exists
    img_url = None
    if current_user.profile_image:
        # We replace backslashes with forward slashes for URL compatibility
        clean_path = current_user.profile_image.replace("\\", "/")
        img_url = f"{base_url}/{clean_path}"

    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "profile_image": img_url, 
        "streak": 5, 
        "points": 1250
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

@router.patch("/users/me")
async def update_profile(
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    # Get the ID instead of the object
    current_user_id: int = Depends(get_current_user_id), 
):
    try:
        # Fetch the user inside the route's own session
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if image:
            ext = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            content = await image.read()
            with open(file_path, "wb") as f:
                f.write(content)

            user.profile_image = file_path

        db.commit()
        db.refresh(user)

        # Build the return URL
        base_url = "http://127.0.0.1:8000"
        img_url = f"{base_url}/{user.profile_image.replace(os.sep, '/')}" if user.profile_image else None
        print(img_url)
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_image": img_url,
            },
        }
    except Exception as e:
        db.rollback()
        print(f"Detailed Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")