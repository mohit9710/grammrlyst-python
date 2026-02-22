from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.sentence import correct_sentence
from app.core.roleplay import get_roleplay_response
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/sentence", tags=["Sentence Correction"])

# --- Models ---

class SentenceRequest(BaseModel):
    sentence: str = Field(..., min_length=1, max_length=500, example="He go to school yesterday.")

class SentenceResponse(BaseModel):
    original: str
    fixed: str
    rule: str = "Grammar & Style"  # Default rule if your model doesn't provide one

class RoleplayRequest(BaseModel):
    role_title: str = Field(..., example="Job Interviewer")
    user_input: str = Field(..., min_length=1)
# --- Router ---

@router.post("/correct")
async def sentence_correct(req: SentenceRequest):
    try:
        # result is now a DICTIONARY, e.g., {"original": "...", "fixed": "...", "rule": "..."}
        result = await run_in_threadpool(correct_sentence, req.sentence)
        
        # FIX: Do not use .strip() on result. Use it on the specific field inside result.
        # The core logic above already handles the stripping now.
        
        return result 
        
    except Exception as e:
        print(f"Route Error: {e}")
        raise HTTPException(status_code=500, detail="Server was unable to process the request.")

@router.post("/roleplay")
async def roleplay_chat(req: RoleplayRequest):
    """
    Handles conversational roleplay while providing grammar feedback.
    """
    try:
        result = await run_in_threadpool(
            get_roleplay_response, 
            req.role_title, 
            req.user_input
        )
        return result
    except Exception as e:
        print(f"Roleplay Route Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="The AI tutor is currently unavailable."
        )