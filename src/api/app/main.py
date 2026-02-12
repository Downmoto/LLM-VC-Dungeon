from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from app.core.config import settings
from app.game.game import GameEngine
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
llm_provider = LLMService()



@app.get("/")
async def root() -> dict[str, Any]:
    """health check endpoint"""
    return {
        "status": "healthy",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_GEN_MODEL,
        "endpoints": {
            "new-game": "/api/new-game",
            "load-game": "/api/load-game",
            "game-turn": "/api/game/turn"
        }
    }


@app.post("/api/new-game", response_model=NewGameResponse)
async def new_game(request: NewGameRequest):
    """start a new game with fresh game state"""
    if not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        # create new game engine instance
        save_path = request.save_path or "data/savegame.json"
        new_game_engine = GameEngine(save_path)
        
        # initialize with fresh game state
        await new_game_engine.init_game(llm_provider)
        
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
    if not llm_provider:
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
    if not llm_provider:
        raise HTTPException(status_code=503, detail="llm provider not initialized")
    
    try:
        (narrative, action) = await game_engine.process_turn(request.user_input, llm_provider, background_tasks)
        return GameTurnResponse(narrative=narrative, action=action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"game turn failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )