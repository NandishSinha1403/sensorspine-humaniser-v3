from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from engine.amr_handler import AMRHandler
from engine.contrastive_decoder import HumanizerEngine
from engine.diagnostic_judge import DiagnosticJudge

app = FastAPI(title="ScholarAI v3 SOTA Backend")
amr_handler = AMRHandler()
# Lazy initialize engines
humanizer_engine = None
judge = None

class HumanizeRequest(BaseModel):
    text: str
    intensity: float = 1.0

@app.get("/")
async def root():
    return {"message": "ScholarAI v3 Backend is running"}

@app.post("/humanize")
async def humanize(request: HumanizeRequest):
    global humanizer_engine, judge
    try:
        # Step 1: Initial AMR Processing
        amr_processed_text = amr_handler.humanize_via_amr(request.text)
        
        # Initialize engines if in Colab environment
        if humanizer_engine is None and os.environ.get("SKIP_LLM_LOAD") != "true":
            humanizer_engine = HumanizerEngine()
            humanizer_engine.load_models()
            judge = DiagnosticJudge(model=humanizer_engine.base_model, tokenizer=humanizer_engine.base_tokenizer)
        
        final_text = amr_processed_text
        confidence_score = 0.85 # Default if models not loaded
        
        if humanizer_engine and judge:
            # Recursive Refinement (Max 2 attempts for efficiency)
            for attempt in range(2):
                prompt = f"Rewrite this text to be more natural and human-like: {final_text if attempt > 0 else amr_processed_text}"
                candidate_text = humanizer_engine.generate_humanized(prompt, alpha=request.intensity * 0.5)
                
                is_human, score = judge.judge(candidate_text, threshold=0.7)
                final_text = candidate_text
                confidence_score = score
                
                if is_human:
                    break
        
        return {
            "original": request.text,
            "amr_intermediate": amr_processed_text,
            "humanized": final_text,
            "confidence_score": round(confidence_score, 2)
        }
    except Exception as e:
        print(f"Error during humanization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
