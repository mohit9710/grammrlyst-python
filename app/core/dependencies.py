from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError # Better error handling
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User  # CRITICAL: Ensure User is imported!
from app.db.purchase import Purchase
from datetime import datetime, timedelta

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token = Depends(security), 
    db: Session = Depends(get_db)
):
    try:
        # 1. Decode the token string using your Secret Key
        payload = jwt.decode(
            token.credentials, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        
        # 2. GET THE USER_ID FROM THE DECODED PAYLOAD
        # This matches the key {"user_id": user.id} you set during Login/Signin
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token is missing user identification"
            )
            
        # 3. Use that ID to fetch the record from the database
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found in database"
            )
            
        return user # This is the object with first_name, last_name, etc.

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials"
        )

def get_current_user_id(token=Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_active_plan(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    purchase = get_active_purchase(user_id, db)

    if not purchase:
        raise HTTPException(
            status_code=403,
            detail="Plan expired or not active"
        )

    return purchase


def get_active_purchase(user_id: int, db: Session):
    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == user_id,
            Purchase.status == "success"
        )
        .order_by(Purchase.created_at.desc())
        .first()
    )

    if not purchase:
        return None

    if purchase.end_date is None:
        return purchase  # lifetime

    if purchase.end_date > datetime.utcnow():
        return purchase

    return None

def has_active_plan(user_id: int, db: Session):
    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.user_id == user_id,
            Purchase.status == "success"
        )
        .order_by(Purchase.created_at.desc())
        .first()
    )
    if not purchase:
        return False

    if purchase.end_date is None:
        return True  # lifetime

    return purchase.end_date > datetime.utcnow()