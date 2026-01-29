from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from contextlib import asynccontextmanager
from app.core.factory import get_llm_provider
from app.core.config import settings


llm_provider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """initialize llm provider on startup and cleanup on shutdown"""
    global llm_provider
    print(f"starting api with ai_stack_mode: {settings.AI_STACK_MODE}")
    llm_provider = get_llm_provider()
    print("llm provider initialized successfully")
    yield
    print("shutting down api")


# pydantic models for request/response
class GenerateTextRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None


class GenerateTextResponse(BaseModel):
    text: str


class ClassifyIntentRequest(BaseModel):
    user_input: str


class ClassifyIntentResponse(BaseModel):
    action: str
    target: str
    confidence: float


# initialize fastapi app
app = FastAPI(
    title="llm-vc-dungeon-api",
    description="backend api for voice-controlled dungeon crawler with llm integration",
    version="0.1.0",
    lifespan=lifespan
)

# cors middleware for svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],  # svelte dev and preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, Any]:
    """health check endpoint"""
    return {
        "status": "healthy",
        "ai_stack_mode": settings.AI_STACK_MODE,
        "provider_initialized": llm_provider is not None,
        "endpoints": {
            "generate": "/api/generate",
            "classify": "/api/classify"
        }
    }


@app.post("/api/generate", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """generate narrative text using the configured llm provider"""
    if not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        text = await llm_provider.generate_text(
            prompt=request.prompt,
            system_prompt=request.system_prompt
        )
        return GenerateTextResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"generation failed: {str(e)}")


@app.post("/api/classify", response_model=ClassifyIntentResponse)
async def classify_intent(request: ClassifyIntentRequest):
    """classify user intent using the configured llm provider"""
    if not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        result = await llm_provider.classify_intent(user_input=request.user_input)
        return ClassifyIntentResponse(
            action=result.get("action", "unknown"),
            target=result.get("target", ""),
            confidence=result.get("confidence", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"classification failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )