from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from contextlib import asynccontextmanager
from app.core.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    """initialize llm provider on startup and cleanup on shutdown"""
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
        "endpoints": {
            "generate": "/api/generate",
            "classify": "/api/classify"
        }
    }

@app.post("/api/generate", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """generate narrative text using the configured llm provider"""
    return GenerateTextResponse(text=request.prompt)

@app.post("/api/classify", response_model=ClassifyIntentResponse)
async def classify_intent(request: ClassifyIntentRequest):
    """classify user intent using the configured llm provider"""
    return ClassifyIntentResponse(
        action="unknown",
        target=request.user_input,
        confidence=0.5
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )