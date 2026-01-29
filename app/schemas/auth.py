from pydantic import BaseModel, EmailStr, constr

class SignUpSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: constr(min_length=8, max_length=72)

class SignInSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=1, max_length=72)

class ResetPasswordSchema(BaseModel):
    token: constr(min_length=10)
    new_password: constr(min_length=8, max_length=72)

class ForgotPasswordSchema(BaseModel):
    email: EmailStr
