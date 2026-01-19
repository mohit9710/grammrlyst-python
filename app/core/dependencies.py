# core/dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM

security = HTTPBearer()

def get_current_user(token=Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
