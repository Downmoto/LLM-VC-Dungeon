from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from app.core.config import settings
from app.game.game import GameEngine
from app.game.intent import classify_intent_programmatic
from app.services.llm import LLMService


# pydantic models for request/response
class NewGameRequest(BaseModel):
    save_path: Optional[str] = None


class NewGameResponse(BaseModel):
    message: str
    game_id: str
    initial_room: str


class LoadGameRequest(BaseModel):
    save_path: Optional[str] = None


class LoadGameResponse(BaseModel):
    message: str
    game_id: str
    current_room: str


class GameTurnRequest(BaseModel):
    user_input: str


class GameTurnResponse(BaseModel):
    narrative: str
    action: Optional[dict] = None


class MapRoomResponse(BaseModel):
    id: str
    exits: dict[str, str]
    is_generated: bool
    is_visited: bool


class GameMapResponse(BaseModel):
    theme: str
    current_room_id: str
    rooms: list[MapRoomResponse]


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
    version="0.1.0"
)

# cors middleware for svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],  # svelte dev and preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize game engine and llm provider
game_engine = GameEngine()
llm_provider: Optional[LLMService] = None
if settings.GAME_MODE.lower() in {"llm", "hybrid"} or settings.ENABLE_LLM_NARRATION:
    llm_provider = LLMService()



@app.get("/")
async def root() -> dict[str, Any]:
    """health check endpoint"""
    provider = settings.LLM_PROVIDER.lower()
    model = settings.OLLAMA_GEN_MODEL
    if provider == "openai":
        model = settings.OPENAI_GEN_MODEL
    elif provider == "google":
        model = settings.GOOGLE_GEN_MODEL
    return {
        "status": "healthy",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_GEN_MODEL,
        "llm_provider": provider,
        "llm_model": model,
        "endpoints": {
            "new-game": "/api/new-game",
            "load-game": "/api/load-game",
            "game-turn": "/api/game/turn",
            "game-map": "/api/game/map",
            "generate": "/api/generate",
            "classify": "/api/classify"
        }
    }


@app.post("/api/generate", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """generate text for diagnostics and development tooling"""
    if llm_provider is not None:
        text = await llm_provider.generate_text(request.prompt, request.system_prompt)
        return GenerateTextResponse(text=text)

    # fallback for programmatic mode so diagnostics remain functional
    prefix = "programmatic mode"
    if request.system_prompt:
        prefix = f"{prefix} ({request.system_prompt[:40]})"
    return GenerateTextResponse(text=f"{prefix}: {request.prompt}")


@app.post("/api/classify", response_model=ClassifyIntentResponse)
async def classify_intent(request: ClassifyIntentRequest):
    """classify intent for diagnostics and development tooling"""
    mode = settings.GAME_MODE.lower()
    intent = classify_intent_programmatic(request.user_input)
    confidence = 0.9 if intent.get("action") != "unknown" else 0.25

    if mode in {"llm", "hybrid"} and llm_provider is not None:
        llm_intent = await llm_provider.classify_intent(request.user_input)
        if mode == "llm" or intent.get("action") == "unknown":
            intent = llm_intent
            confidence = 0.95 if intent.get("action") != "unknown" else 0.3

    target = intent.get("target", "")
    if not target and intent.get("action") == "move":
        target = intent.get("direction", "")

    return ClassifyIntentResponse(
        action=intent.get("action", "unknown"),
        target=target,
        confidence=confidence,
    )


@app.post("/api/new-game", response_model=NewGameResponse)
async def new_game(request: NewGameRequest):
    """start a new game with fresh game state"""
    if settings.GAME_MODE.lower() == "llm" and not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        # create new game engine instance
        save_path = request.save_path or "data/savegame.json"
        new_game_engine = GameEngine(save_path)
        
        # initialize with fresh game state
        await new_game_engine.init_game(llm_provider, force_new=True)
        
        # replace global game engine
        global game_engine
        game_engine = new_game_engine
        
        # get initial state
        state = await game_engine.get_state(llm_provider)
        current_room = state.rooms[state.player.current_room_id]
        
        return NewGameResponse(
            message="new game started successfully",
            game_id=state.player.current_room_id,
            initial_room=current_room.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to start new game: {str(e)}")


@app.post("/api/load-game", response_model=LoadGameResponse)
async def load_game_endpoint(request: LoadGameRequest):
    """load an existing game from save file"""
    if settings.GAME_MODE.lower() == "llm" and not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        save_path = request.save_path or "data/savegame.json"
        loaded_game_engine = GameEngine(save_path)
        
        # load existing game state
        await loaded_game_engine.init_game(llm_provider)
        
        # replace global game engine
        global game_engine
        game_engine = loaded_game_engine
        
        # get current state
        state = await game_engine.get_state(llm_provider)
        current_room = state.rooms[state.player.current_room_id]
        
        return LoadGameResponse(
            message="game loaded successfully",
            game_id=state.player.current_room_id,
            current_room=current_room.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to load game: {str(e)}")


@app.post("/api/game/turn", response_model=GameTurnResponse)
async def process_game_turn(request: GameTurnRequest, background_tasks: BackgroundTasks):
    """process a game turn with user input"""
    if settings.GAME_MODE.lower() == "llm" and not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        (narrative, action) = await game_engine.process_turn(request.user_input, llm_provider, background_tasks)
        return GameTurnResponse(narrative=narrative, action=action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"game turn failed: {str(e)}")


@app.get("/api/game/map", response_model=GameMapResponse)
async def get_game_map():
    """return room graph metadata for frontend map rendering"""
    try:
        state = await game_engine.get_state(llm_provider)
        rooms = [
            MapRoomResponse(
                id=room.id,
                exits=room.exits,
                is_generated=room.is_generated,
                is_visited=room.is_visited,
            )
            for room in state.rooms.values()
        ]
        return GameMapResponse(
            theme=state.theme,
            current_room_id=state.player.current_room_id,
            rooms=rooms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to fetch game map: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )