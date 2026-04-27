from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, TEXT, ForeignKey, Enum, UniqueConstraint
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func
import enum

class RewardType(str, enum.Enum):
    days = "days"
    coins = "coins"
    cash = "cash"


class RewardStatus(str, enum.Enum):
    pending = "pending"
    credited = "credited"


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    referral_id = Column(
        BigInteger,
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False
    )

    reward_type = Column(
        Enum(RewardType),
        nullable=False
    )

    reward_value = Column(
        Integer,
        nullable=False
    )

    status = Column(
        Enum(RewardStatus),
        default=RewardStatus.pending
    )

    credited_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )