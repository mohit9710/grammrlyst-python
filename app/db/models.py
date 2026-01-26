from sqlalchemy import Column, Integer, String, Boolean, DateTime, TEXT, ForeignKey, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

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
    __tablename__ = "Sentences"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(TEXT, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')
    char_count = Column(Integer)

# New Spelling Model
class SpellingChallenge(Base):
    __tablename__ = "SpellingChallenges"
    id = Column(Integer, primary_key=True, index=True)
    wrong_version = Column(String(255), nullable=False)
    right_version = Column(String(255), nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')

class ScrambleChallenge(Base):
    __tablename__ = "ScrambleChallenges"

    id = Column(Integer, primary_key=True, index=True)
    original_word = Column(String(100), nullable=False)
    scrambled_word = Column(String(100), nullable=False)
    hint = Column(TEXT, nullable=True)
    difficulty = Column(Enum('easy', 'medium', 'hard'), default='medium')