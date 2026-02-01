from pydantic import BaseModel, EmailStr, constr, field_validator
from datetime import datetime
from typing import Optional

class SignUpSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: constr(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class SignInSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=1, max_length=72)

class ResetPasswordSchema(BaseModel):
    token: constr(min_length=10)
    new_password: constr(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class XPUpdateRequest(BaseModel):
    points_to_add: int
    is_bonus: bool = False

class ActivityLogResponse(BaseModel):
    id: int
    activity_type: str
    description: str
    points_earned: int
    created_at: datetime

    class Config:
        from_attributes = True # SQLAlchemy object ko JSON mein convert karne ke liye

# 3. User Stats Schema: Dashboard ke liye
class UserStatsResponse(BaseModel):
    total_xp: int
    bonus: int
    points: int
    streak: int