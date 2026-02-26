from sqlalchemy import Column, Integer, String, Boolean, DateTime, TEXT, ForeignKey, Enum, UniqueConstraint
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_image = Column(String(255), nullable=True)
    
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)

    # FIXED: Duplicate columns removed and set to Integer
    streak = Column(Integer, default=0)
    points = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    bonus = Column(Integer, default=0)
    
    # Consistency check: Use Date for logic, DateTime for timestamps
    last_login_date = Column(DateTime, nullable=True) 
    last_bonus_date = Column(DateTime, nullable=True)

    # Relationships
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    is_paid = Column(Integer, default=0)

class Verbs(Base):
    __tablename__ = "verbs"
    id = Column(Integer, primary_key=True, index=True)
    base = Column(String(50),  nullable=False)
    past = Column(String(50), nullable=False)
    past_participle = Column(String(50), nullable=False)
    meaning = Column(TEXT, nullable=False) # Added TEXT type
    example = Column(TEXT, nullable=False) # Added TEXT type
    type = Column(TEXT, nullable=False) # Added TEXT type

class GrammarTopic(Base):
    __tablename__ = "grammar" # Updated for consistency
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
    # Added relationship to questions
    questions = relationship("QuizQuestion", back_populates="lesson", cascade="all, delete-orphan")

# --- NEW QUIZ MODELS ---

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

class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(TEXT, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')
    char_count = Column(Integer)

# New Spelling Model
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

class DailyTip(Base):
    __tablename__ = "daily_tips"

    id = Column(Integer, primary_key=True, index=True)
    wrong_sentence = Column(TEXT, nullable=False)
    correct_sentence = Column(TEXT, nullable=False)
    explanation = Column(TEXT, nullable=False)
    level = Column(Enum("beginner", "intermediate", "advanced"), default="beginner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserVerbProgress(Base):
    __tablename__ = "user_verb_progress"

    id = Column(Integer, primary_key=True, index=True)
    # Add ForeignKey here 👇
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    verb_id = Column(Integer, ForeignKey("verbs.id", ondelete="CASCADE"), index=True)

    views = Column(Integer, default=0)
    stage = Column(Integer, default=0) 

    first_view = Column(DateTime, default=datetime.utcnow)
    last_view = Column(DateTime, default=datetime.utcnow)

    # Prevent duplicate rows for the same user + verb
    __table_args__ = (
        UniqueConstraint('user_id', 'verb_id', name='_user_verb_uc'),
    )

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    activity_type = Column(String(50))  # e.g., "GAME_WIN", "BONUS_CLAIM"
    description = Column(String(255))
    points_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    scenario = Column(TEXT, nullable=False)
    instruction = Column(TEXT)
    avatar = Column(String(10))
    voice_type = Column(String(50))