from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI()

model_id = "vennify/t5-base-grammar-correction"
save_path = "../model"
# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

# MySQL connection (update with your credentials)
DATABASE_URL = "mysql+pymysql://root@localhost:3306/grammrlyst"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ---------------------------
# Database Models
# ---------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    contact = Column(String(20), nullable=True)
    role = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    join_date = Column(DateTime, default=datetime.utcnow)

    chats = relationship("Chat", back_populates="user")


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_message = Column(Text, nullable=False)
    bot_reply = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


# Create tables
Base.metadata.create_all(bind=engine)

# ---------------------------
# Pydantic Models
# ---------------------------
class RegisterModel(BaseModel):
    username: str
    contact: Optional[str] = None
    email: str
    password_hash: str
    role:str

class LoginModel(BaseModel):
    username: str
    password_hash: str

class ChatModel(BaseModel):
    username: str
    message: str

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Routes
# ---------------------------

@app.get("/")
def home():
    return {"message": "Hello, FastAPI with MySQL!"}

# Register user
@app.post("/register")
def register(user: RegisterModel):
    db = next(get_db())
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password
    hashed_pw = bcrypt.hashpw(user.password_hash.encode('utf-8'), bcrypt.gensalt())

    new_user = User(
        username=user.username,
        contact=user.contact,
        email=user.email,
        role=user.role,
        password_hash=hashed_pw.decode("utf-8")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}

# Login user
@app.post("/login")
def login(user: LoginModel):
    db = next(get_db())
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # Check password
    if not bcrypt.checkpw(user.password_hash.encode('utf-8'), db_user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": "Login successful"}

# User profile
@app.get("/userprofile/{username}")
def userProfile(username: str):
    db = next(get_db())
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    return {
        "username": db_user.username,
        "email": db_user.email,
        "contact": db_user.contact,
        "join_date": db_user.join_date
    }

# Chat with bot
@app.post("/chat")
def chat(data: ChatModel):
    db = next(get_db())
    db_user = db.query(User).filter(User.username == data.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    # Example bot logic
    if "hello" in data.message.lower():
        bot_reply = "Hi there! How can I help you today?"
    else:
        bot_reply = check_grammer(data.message.lower())

    chat_entry = Chat(
        user_id=db_user.id,
        user_message=data.message,
        bot_reply=bot_reply,
    )
    db.add(chat_entry)
    db.commit()

    return {"user_message": data.message, "bot_reply": bot_reply}

# Get chat history
@app.get("/chat/history/{username}")
def get_chat_history(username: str):
    db = next(get_db())
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    chats = db.query(Chat).filter(Chat.user_id == db_user.id).all()
    history = [
        {
            "user_message": c.user_message,
            "bot_reply": c.bot_reply,
            "timestamp": c.created_at
        }
        for c in chats
    ]
    return {"chat_history": history}

def check_grammer(input_sentence):
    # Input sentence (with grammatical error)

    # Prepend the task prefix (required for T5 models)
    input_text = "grammar: " + input_sentence

    # Tokenize input
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

    # Generate output (corrected sentence)
    outputs = model.generate(
        inputs,
        max_length=128,
        num_beams=5,
        early_stopping=True
    )

    # Decode and print the result
    corrected_sentence = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return corrected_sentence
