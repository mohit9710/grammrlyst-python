# app/db/models/purchase.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float, Boolean
from datetime import datetime
from app.db.session import Base
from sqlalchemy.orm import relationship

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)   # free, monthly, yearly, lifetime
    price = Column(Float)
    duration = Column(Integer, nullable=True)  # null for lifetime
    is_active = Column(Boolean, default=True)

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))

    payment_id = Column(String(255))
    order_id = Column(String(255))
    signature = Column(String(255))

    status = Column(String(255), default="pending")  # pending, success, failed

    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan")