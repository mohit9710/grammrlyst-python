from pydantic import BaseModel, EmailStr

class SignUpSchema(BaseModel):
    email: EmailStr
    password: str

class SignInSchema(BaseModel):
    email: EmailStr
    password: str