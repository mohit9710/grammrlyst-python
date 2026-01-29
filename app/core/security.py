from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_password(password: str) -> str:
    # ensures bcrypt never receives >72 bytes
    return password[:72]

def hash_password(password: str):
    return pwd_context.hash(_normalize_password(password))

def verify_password(password: str, hashed: str):
    return pwd_context.verify(_normalize_password(password), hashed)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def generate_email_token():
    return secrets.token_urlsafe(32)

def generate_reset_token():
    return secrets.token_urlsafe(32)
