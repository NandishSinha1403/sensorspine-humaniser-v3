from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os
from tasks import celery_app, process_humanization
from celery.result import AsyncResult
from engine.security import verify_token, create_access_token
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ScholarAI v3 SOTA Backend (Async & Secure)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - In production, this should be restricted to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HumanizeRequest(BaseModel):
    text: str = Field(..., max_length=3000)
    intensity: float = Field(default=1.0, ge=0, le=2.0)

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/")
async def root():
    return {"message": "ScholarAI v3 Async & Secure Backend is running"}

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request):
    """
    Mock login endpoint to get a JWT token.
    In a real system, you would verify username/password here.
    """
    access_token = create_access_token(data={"sub": "demo_user"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/humanize")
@limiter.limit("10/hour") # Restrict expensive GPU tasks
async def humanize(request: Request, body: HumanizeRequest, user_id: str = Depends(verify_token)):
    """Enqueue a humanization task and return a task ID. Protected by JWT."""
    try:
        task = process_humanization.delay(body.text, body.intensity)
        return {"task_id": task.id, "status": "pending", "user": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
@limiter.limit("60/minute") # Higher limit for status checks
async def get_status(request: Request, task_id: str, user_id: str = Depends(verify_token)):
    """Check the status of a humanization task. Protected by JWT."""
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif result.state == "SUCCESS":
        return result.result
    elif result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.info)}
    else:
        return {"task_id": task_id, "status": result.state}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
