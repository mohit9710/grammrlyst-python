from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt

app = FastAPI()

# MongoDB connection
# client = MongoClient("mongodb://localhost:27017")  # change if needed
client = MongoClient("mongodb+srv://newxyz8:LidC7VRShmpFUvpH@grammrlyst.0fhix5t.mongodb.net/")

db = client["grammrlyst"]
users_collection = db["users_db"]

# Pydantic models
class RegisterModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

@app.get("/")
def home():
    return {"message": "Hello, FastAPI with MongoDB!"}

# Register user
@app.post("/register")
def register(user: RegisterModel):
    # Check if username exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password
    hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    # Insert into MongoDB
    users_collection.insert_one({
        "username": user.username,
        "password": hashed_pw
    })

    return {"message": "User registered successfully"}

# Login user
@app.post("/login")
def login(user: LoginModel):
    # Find user
    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # Check password
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": "Login successful"}
