from pydantic import BaseModel, EmailStr

class SignUpSchema(BaseModel):
    # name : str
    first_name : str
    last_name : str
    email: EmailStr
    password: str

class SignInSchema(BaseModel):
    email: EmailStr
    password: str