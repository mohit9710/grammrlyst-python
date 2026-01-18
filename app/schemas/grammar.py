from pydantic import BaseModel
from typing import List, Optional

# --- Lesson Schemas ---
class LessonBase(BaseModel):
    title: str
    formula: Optional[str] = None
    example_sentence: Optional[str] = None
    content_body: Optional[str] = None

class LessonCreate(LessonBase):
    topic_id: int

class LessonResponse(LessonBase):
    id: int
    
    class Config:
        from_attributes = True # Necessary for SQLAlchemy compatibility

# --- Topic Schemas ---
class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    level: str
    display_order: int = 0

class TopicResponse(TopicBase):
    id: int
    lessons: List[LessonResponse] = [] # Nests the lessons inside the topic

    class Config:
        from_attributes = True