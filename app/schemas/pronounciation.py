from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TextBase(BaseModel):
    content: str
    difficulty_level: str
    category: Optional[str] = "General"

class TextResponse(TextBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True