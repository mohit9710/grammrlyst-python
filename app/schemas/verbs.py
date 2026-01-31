from pydantic import BaseModel
from typing import Optional

class VerbProgressResponse(BaseModel):
    views: int
    stage: int

class VerbResponse(BaseModel):
    id: int
    base: str
    past: Optional[str] = None
    past_participle: Optional[str] = None
    meaning: Optional[str] = None
    example: Optional[str] = None
    type: Optional[str] = None
    progress: Optional[VerbProgressResponse] = None  # ✅ Add this

    class Config:
        from_attributes = True

class VerbViewSchema(BaseModel):
    verb_id: int
