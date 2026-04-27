from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, TEXT, ForeignKey, Enum, UniqueConstraint
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func
import enum


class ReferralType(str, enum.Enum):
    student = "student"
    institute = "institute"


class ReferralStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(BigInteger, primary_key=True, index=True)

    referrer_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    referee_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    referral_type = Column(
        Enum(ReferralType),
        default=ReferralType.student,
        nullable=True
    )

    referral_code = Column(String(255), nullable=True)

    status = Column(
        Enum(ReferralStatus),
        default=ReferralStatus.pending,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint('referrer_id', 'referee_id', name='unique_referral_pair'),
    )