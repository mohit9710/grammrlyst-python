from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, TEXT, ForeignKey, Enum, UniqueConstraint, DECIMAL
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func
import enum

# ===================== USERS =====================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image = Column(String(255), nullable=True)
    
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)

    streak = Column(Integer, default=0)
    points = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    bonus = Column(Integer, default=0)
    
    last_login_date = Column(DateTime, nullable=True) 
    last_bonus_date = Column(DateTime, nullable=True)

    is_paid = Column(Integer, default=0)

    referral_code = Column(String(50), unique=True, index=True)
    referred_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    # Relationships
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")

# ===================== VERBS =====================
class Verbs(Base):
    __tablename__ = "verbs"
    id = Column(Integer, primary_key=True, index=True)
    base = Column(String(50), nullable=False)
    past = Column(String(50), nullable=False)
    past_participle = Column(String(50), nullable=False)
    meaning = Column(TEXT, nullable=False)
    example = Column(TEXT, nullable=False)
    type = Column(TEXT, nullable=False)

# ===================== GRAMMAR =====================
class GrammarTopic(Base):
    __tablename__ = "grammar"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    level = Column(Enum('Beginner', 'Intermediate', 'Advanced', 'Native'), default='Beginner')
    display_order = Column(Integer, default=0)

    lessons = relationship("GrammarLesson", back_populates="topic", cascade="all, delete-orphan")

class GrammarLesson(Base):
    __tablename__ = "grammar_lessons"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("grammar.id", ondelete="CASCADE"))
    title = Column(String(100), nullable=False)
    formula = Column(String(255))
    example_sentence = Column(TEXT)
    content_body = Column(TEXT)

    topic = relationship("GrammarTopic", back_populates="lessons")
    questions = relationship("QuizQuestion", back_populates="lesson", cascade="all, delete-orphan")

# ===================== QUIZ =====================
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("grammar_lessons.id", ondelete="CASCADE"))
    question_text = Column(TEXT, nullable=False)

    lesson = relationship("GrammarLesson", back_populates="questions")
    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")

class QuizOption(Base):
    __tablename__ = "quiz_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    option_text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("QuizQuestion", back_populates="options")

# ===================== SENTENCES =====================
class Sentence(Base):
    __tablename__ = "sentences"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(TEXT, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')
    char_count = Column(Integer)

# ===================== SPELLING =====================
class SpellingChallenge(Base):
    __tablename__ = "spellingchallenges"
    id = Column(Integer, primary_key=True, index=True)
    wrong_version = Column(String(255), nullable=False)
    right_version = Column(String(255), nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')

class ScrambleChallenge(Base):
    __tablename__ = "scramblechallenges"
    id = Column(Integer, primary_key=True, index=True)
    original_word = Column(String(100), nullable=False)
    scrambled_word = Column(String(100), nullable=False)
    hint = Column(TEXT, nullable=True)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')

# ===================== DAILY TIPS =====================
class DailyTip(Base):
    __tablename__ = "daily_tips"
    id = Column(Integer, primary_key=True, index=True)
    wrong_sentence = Column(TEXT, nullable=False)
    correct_sentence = Column(TEXT, nullable=False)
    explanation = Column(TEXT, nullable=False)
    level = Column(Enum("beginner", "intermediate", "advanced"), default="beginner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ===================== USER VERB PROGRESS =====================
class UserVerbProgress(Base):
    __tablename__ = "user_verb_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    verb_id = Column(Integer, ForeignKey("verbs.id", ondelete="CASCADE"), index=True)
    views = Column(Integer, default=0)
    stage = Column(Integer, default=0)
    first_view = Column(DateTime, default=datetime.utcnow)
    last_view = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'verb_id', name='_user_verb_uc'),
    )

# ===================== USER ACTIVITY =====================
class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    activity_type = Column(String(50))
    description = Column(String(255))
    points_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")

# ===================== ROLES =====================
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    scenario = Column(TEXT, nullable=False)
    instruction = Column(TEXT)
    avatar = Column(String(10))
    voice_type = Column(String(50))

class DifficultyLevel(str, enum.Enum):
    Easy = "Easy"
    Medium = "Medium"
    Hard = "Hard"

class PronunciationText(Base):
    __tablename__ = "pronunciation_texts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(TEXT, nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.Easy)
    category = Column(String(50), default="General")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InstituteProfile(Base):
    __tablename__ = "institute_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    institute_name = Column(String(255))
    contact_person = Column(String(255))
    phone = Column(String(20))
    website = Column(String(255))

    created_at = Column(DateTime, server_default=func.now())

class EarningStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    paid = "paid"
    rejected = "rejected"


class InstituteEarning(Base):
    __tablename__ = "institute_earnings"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Relations
    institute_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    referred_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    referral_id = Column(
        Integer,
        ForeignKey("referrals.id", ondelete="SET NULL"),
        nullable=True
    )

    # 💰 Commission data
    base_amount = Column(DECIMAL(10, 2), nullable=False)        # e.g. 1000
    commission_percent = Column(Integer, nullable=False)        # 10 / 20 / 30
    commission_amount = Column(DECIMAL(10, 2), nullable=False)  # e.g. 200

    # 🔄 Status lifecycle
    status = Column(
        Enum(EarningStatus),
        default=EarningStatus.pending,
        nullable=False,
        index=True
    )

    # 💳 Payout tracking
    payout_reference = Column(String(255), nullable=True)
    payout_date = Column(DateTime, nullable=True)

    # 🔐 Refund safety
    is_refunded = Column(Boolean, default=False)
    refunded_at = Column(DateTime, nullable=True)

    # 🕒 Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())