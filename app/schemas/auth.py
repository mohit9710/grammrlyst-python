from pydantic import BaseModel, EmailStr, constr, field_validator

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
