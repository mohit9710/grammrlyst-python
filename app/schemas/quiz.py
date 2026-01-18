from pydantic import BaseModel
from typing import List, Optional

# Schema for the Options (A, B, C, D)
class QuizOptionResponse(BaseModel):
    id: int
    option_text: str
    is_correct: bool # Optional: Remove this if you don't want the frontend to see the answer early

    class Config:
        from_attributes = True

# Schema for the Question itself
class QuizQuestionResponse(BaseModel):
    id: int
    lesson_id: int
    question_text: str
    # This nests the options list inside the question object
    options: List[QuizOptionResponse] 

    class Config:
        from_attributes = True