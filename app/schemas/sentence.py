from pydantic import BaseModel
from typing import Optional

class SentenceSchema(BaseModel):
    id: int
    content: str
    difficulty: str

    class Config:
        from_attributes = True

class SpellingSchema(BaseModel):
    id: int
    wrong_version: str
    right_version: str
    difficulty: str
    class Config:
        from_attributes = True

class ScrambleSchema(BaseModel):
    id: int
    original_word: str
    scrambled_word: str
    hint: Optional[str] = None
    difficulty: str

    class Config:
        from_attributes = True