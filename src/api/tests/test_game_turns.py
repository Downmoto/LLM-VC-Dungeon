import pytest

from app.core.config import settings
from app.game.game import GameEngine
from app.game.models import Enemy, EnemyType, GameState, Item, ItemType, PlayerState, Room


@pytest.fixture
def game_engine_with_state(tmp_path):
    engine = GameEngine(save_path=str(tmp_path / "savegame.json"))

    room_0 = Room(
        id="room_0",
        exits={"north": "room_1"},
        description="you are in the entry room",
        items=[Item(name="iron key", type=ItemType.KEY)],
        enemies=[Enemy(name="cave rat", type=EnemyType.BEAST, hp=10, max_hp=10)],
        is_generated=True,
    )
    room_1 = Room(
        id="room_1",
        exits={"south": "room_0"},
        description="you are in the northern room",
        is_generated=True,
    )

    engine.state = GameState(
        theme="test dungeon",
        player=PlayerState(current_room_id="room_0"),
        rooms={"room_0": room_0, "room_1": room_1},
    )
    return engine


@pytest.mark.asyncio
async def test_process_turn_move_uses_programmatic_parser(game_engine_with_state):
    old_mode = settings.GAME_MODE
    old_narration = settings.ENABLE_LLM_NARRATION
    settings.GAME_MODE = "programmatic"
    settings.ENABLE_LLM_NARRATION = False

    try:
        narrative, action = await game_engine_with_state.process_turn("go north", None)
    finally:
        settings.GAME_MODE = old_mode
        settings.ENABLE_LLM_NARRATION = old_narration

    assert action["action"] == "move"
    assert game_engine_with_state.state.player.current_room_id == "room_1"
    assert "you move north" in narrative.lower()


@pytest.mark.asyncio
async def test_process_turn_take_item(game_engine_with_state):
    old_mode = settings.GAME_MODE
    settings.GAME_MODE = "programmatic"

    try:
        narrative, action = await game_engine_with_state.process_turn("take iron key", None)
    finally:
        settings.GAME_MODE = old_mode

    assert action["action"] == "take"
    assert "you took the iron key" in narrative.lower()
    assert len(game_engine_with_state.state.player.inventory) == 1
    assert game_engine_with_state.state.player.inventory[0].name == "iron key"


@pytest.mark.asyncio
async def test_process_turn_attack_enemy(game_engine_with_state):
    old_mode = settings.GAME_MODE
    settings.GAME_MODE = "programmatic"

    try:
        narrative, action = await game_engine_with_state.process_turn("attack cave rat", None)
    finally:
        settings.GAME_MODE = old_mode

    assert action["action"] == "attack"
    assert "you defeated the cave rat" in narrative.lower()
    current_room = game_engine_with_state.state.rooms["room_0"]
    assert len(current_room.enemies) == 0
