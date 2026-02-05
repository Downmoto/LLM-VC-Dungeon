import json
import os
from .models import GameState

def save_game(state: GameState, filepath: str):
    """Serializes the GameState to JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(state.model_dump_json(indent=2))

def load_game(filepath: str) -> GameState:
    """Deserializes JSON back to GameState."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Save file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
        return GameState.model_validate_json(content)
