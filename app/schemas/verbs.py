from pydantic import BaseModel

class VerbResponse(BaseModel):
    id: int
    base: str
    past: str
    past_participle: str
    meaning: str | None
    example: str | None

    class Config:
        orm_mode = True
