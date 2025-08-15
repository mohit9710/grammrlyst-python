from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional

app = FastAPI()

# MongoDB connection
# client = MongoClient("mongodb://localhost:27017")  # change if needed
client = MongoClient("mongodb+srv://newxyz8:LidC7VRShmpFUvpH@grammrlyst.0fhix5t.mongodb.net/")

db = client["grammrlyst"]
users_collection = db["users_db"]
chat_collection = db["chat_db"]

# Pydantic models
class RegisterModel(BaseModel):
    username: str
    contact: int
    email: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class ChatModel(BaseModel):
    username: str
    message: str

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

@app.get("/userprofile/{username}")
def userProfile(username:str):
    db_user = users_collection.find_one({"username": username})
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    user_data = list(users_collection.find({"username": username}, {"_id": 0}))
    return {"user_profile": user_data}

# Chat with bot
@app.post("/chat")
def chat(data: ChatModel):
    db_user = users_collection.find_one({"username": data.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # Example bot logic (you can replace this with an AI model)
    if "hello" in data.message.lower():
        bot_reply = "Hi there! How can I help you today?"
    else:
        bot_reply = check_grammer(data.message.lower())
        # bot_reply = "I’m just a simple bot for now, but I’ll get smarter soon!"

    # Save to MongoDB
    chat_entry = {
        "username": data.username,
        "user_message": data.message,
        "bot_reply": bot_reply,
        "timestamp": datetime.utcnow()
    }
    chat_collection.insert_one(chat_entry)

    return {"user_message": data.message, "bot_reply": bot_reply}

# Get chat history for a user
@app.get("/chat/history/{username}")
def get_chat_history(username: str):
    db_user = users_collection.find_one({"username": username})
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    history = list(chat_collection.find({"username": username}, {"_id": 0}))
    return {"chat_history": history}

def check_grammer(input_sentence):
    # Input sentence (with grammatical error)

    # Prepend the task prefix (required for T5 models)
    input_text = "grammar: " + input_sentence
    return False
