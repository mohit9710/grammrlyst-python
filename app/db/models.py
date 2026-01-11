from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

class Verbs(Base):
    __tablename__ = "verbs"

    id = Column(Integer, primary_key=True, index=True)
    base = Column(String(50),  nullable=False)
    past = Column(String(50), nullable=False)
    past_participle = Column(String(50), nullable=False)
    meaning = Column(nullable=False)
    example = Column(nullable=False)