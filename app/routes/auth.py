from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models import User, Verbs, InstituteProfile
from firebase_admin import storage
from app.schemas.auth import SignUpSchema, SignInSchema, ResetPasswordSchema, ForgotPasswordSchema, FirebaseToken, PartnerApplySchema
from app.core.security import hash_password, verify_password, create_token, generate_email_token, generate_reset_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.dependencies import get_current_user, get_current_user_id
from app.core.mail import send_verification_email, send_reset_password_email
import uuid, os, httpx
from google.oauth2 import id_token
from google.auth.transport import requests
from app.db.referral import Referral, ReferralType, ReferralStatus
from app.db.referralReward import ReferralReward, RewardStatus, RewardType
import random

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

    referrer = None
    if payload.referral_code:
        referrer = db.query(User).filter(
            User.referral_code == payload.referral_code
        ).first()

        if not referrer:
            referrer = None

        # if not referrer:
        #     raise HTTPException(status_code=400, detail="Invalid referral code")

        # if referrer.email == payload.email:
        #     raise HTTPException(status_code=400, detail="You cannot use your own referral code")

    token = generate_email_token()
    # print(payload)
    user = User(
        # name=payload.first_name+" "+payload.last_name,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password=hash_password(payload.password),
        email_verification_token=token,
        is_email_verified=False,
        referred_by=referrer.id if referrer else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user.referral_code = f"GRM{user.id}"
    db.commit()

    if referrer:
        referral = Referral(
            referrer_id=referrer.id,
            referee_id=user.id,
            referral_type=ReferralType.student,
            referral_code=referrer.referral_code,
            status=ReferralStatus.pending
        )
        db.add(referral)
        db.commit()

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
            "email": user.email,
            "referral_code": user.referral_code
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
def get_profile(current_user: User = Depends(get_current_user)):
    base_url = "http://127.0.0.1:9000"
    img_url = None
    if current_user.profile_image:
        clean_path = current_user.profile_image.replace("\\", "/")
        img_url = f"{base_url}/{clean_path}"

    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "profile_image": current_user.profile_image, 
        "streak": current_user.streak,
        "points": current_user.points,
        "bonus": current_user.bonus,
        "total_xp": current_user.total_xp,
        "is_paid": current_user.is_paid,
        "last_login": current_user.last_login_date # Added for FE tracking
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
    current_user_id: int = Depends(get_current_user_id), 
):
    try:
        user = db.query(User).filter(User.id == current_user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Basic fields update
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        # Firebase Image Update Logic
        if image:
            # 1. Validation (Strictly Image Only)
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only images are allowed")

            # 2. Purani image delete karein (Optional but Recommended)
            # Agar user.profile_image mein pehle se koi Firebase URL hai
            if user.profile_image and "firebasestorage.googleapis.com" in user.profile_image:
                try:
                    # URL se file path nikalna (e.g., 'avatars/xyz.png')
                    # Firebase URL se path extract karne ke liye logic
                    old_blob_path = user.profile_image.split("/o/")[1].split("?")[0].replace("%2F", "/")
                    bucket = storage.bucket()
                    old_blob = bucket.blob(old_blob_path)
                    if old_blob.exists():
                        old_blob.delete()
                except Exception as e:
                    print(f"Old file delete failed: {e}")

            # 3. Nayi file upload karein
            ext = image.filename.split(".")[-1].lower()
            filename = f"grammrlyst/userprofile/{uuid.uuid4()}.{ext}"
            
            bucket = storage.bucket()
            blob = bucket.blob(filename)
            
            content = await image.read()
            blob.upload_from_string(content, content_type=image.content_type)
            
            # 4. Public URL banayein aur DB mein save karein
            blob.make_public()
            user.profile_image = blob.public_url

        db.commit()
        db.refresh(user)

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_image": user.profile_image, # Direct Firebase URL
            },
        }
    except Exception as e:
        db.rollback()
        print(f"Detailed Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google-login")
def google_login(data: FirebaseToken, db: Session = Depends(get_db)):

    try:
        idinfo = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            "996427956752-kdipj4a4e9v2p4s05roqpqgf8iho5i26.apps.googleusercontent.com"
        )

        email = idinfo["email"]
        name = idinfo.get("name")
        google_id = idinfo["sub"]

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                email=email,
                first_name=name,
                is_email_verified=1
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

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "email": email,
            "name": name
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google Token")

@router.post("/completelesson")
def complete_lesson(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        referral = db.query(Referral).filter(
            Referral.referee_id == current_user.id,
            Referral.status == ReferralStatus.pending
        ).first()

        if not referral:
            return {
                "message": "No pending referral found",
                "reward": None
            }

        # 🔒 Prevent duplicate reward
        existing_reward = db.query(ReferralReward).filter(
            ReferralReward.referral_id == referral.id,
            ReferralReward.user_id == referral.referrer_id
        ).first()

        if existing_reward:
            return {
                "message": "Reward already credited",
                "reward": {
                    "type": existing_reward.reward_type,
                    "value": existing_reward.reward_value
                }
            }

        # ✅ Update referral
        referral.status = ReferralStatus.completed
        referral.completed_at = datetime.utcnow()

        # ✅ Create reward
        reward = ReferralReward(
            user_id=referral.referrer_id,
            referral_id=referral.id,
            reward_type=RewardType.days,
            reward_value=3,
            status=RewardStatus.credited
        )

        db.add(reward)
        db.commit()
        db.refresh(reward)

        return {
            "message": "Referral completed & reward credited",
            "reward": {
                "type": reward.reward_type,
                "value": reward.reward_value
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/partner/apply")
def apply_partner(payload: PartnerApplySchema, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == payload.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    temp_password = f"inst{random.randint(1000,9999)}"

    token = generate_email_token()

    user = User(
        email=payload.email,
        first_name=payload.contact_person,
        password=hash_password(temp_password),
        is_email_verified=False,
        email_verification_token=token,
        referred_by="institute"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user.referral_code = f"INST{user.id}"
    db.commit()

    profile = InstituteProfile(
        user_id=user.id,
        institute_name=payload.institute_name,
        contact_person=payload.contact_person,
        phone=payload.phone,
        website=payload.website
    )

    db.add(profile)
    db.commit()

    return {
        "message": "Partner registered successfully",
        "referral_code": user.referral_code
    }