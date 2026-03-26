import pytest
from typing import cast

from app.core.config import settings
from app.game import game as game_module
from app.game.game import GameEngine
from app.game.models import Enemy, EnemyType, GameState, Item, ItemType, PlayerState, Room
from app.services.llm import LLMService


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
async def test_process_turn_take_item_with_conversational_input(game_engine_with_state):
    old_mode = settings.GAME_MODE
    settings.GAME_MODE = "programmatic"

    try:
        narrative, action = await game_engine_with_state.process_turn("i grab the iron key", None)
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


class _FailingLLMService:
    async def classify_intent(self, user_input: str):
        raise RuntimeError("429 RESOURCE_EXHAUSTED. Please retry in 48.3s")


class _TrackingLLMService:
    def __init__(self):
        self.calls = 0

    async def classify_intent(self, user_input: str):
        self.calls += 1
        return {"action": "look"}

    async def generate_text(self, prompt: str, system_prompt: str | None = None):
        return "you scan the room and trace each shadowed corner."


class _NarrationEchoLLMService:
    def __init__(self):
        self.last_prompt = ""

    async def generate_text(self, prompt: str, system_prompt: str | None = None):
        self.last_prompt = prompt
        return "you move north. you are in the northern room"


@pytest.mark.asyncio
async def test_process_turn_llm_quota_raises_when_strict_llm_mode(game_engine_with_state):
    old_mode = settings.GAME_MODE
    old_narration = settings.ENABLE_LLM_NARRATION
    settings.GAME_MODE = "llm"
    settings.ENABLE_LLM_NARRATION = False

    try:
        with pytest.raises(RuntimeError, match="intent classification failed"):
            await game_engine_with_state.process_turn("go north", _FailingLLMService())
    finally:
        settings.GAME_MODE = old_mode
        settings.ENABLE_LLM_NARRATION = old_narration


@pytest.mark.asyncio
async def test_process_turn_llm_uses_llm_even_for_known_programmatic_intent(game_engine_with_state):
    old_mode = settings.GAME_MODE
    old_narration = settings.ENABLE_LLM_NARRATION
    settings.GAME_MODE = "llm"
    settings.ENABLE_LLM_NARRATION = False

    tracking_llm = _TrackingLLMService()
    try:
        narrative, action = await game_engine_with_state.process_turn("where am i", tracking_llm)
    finally:
        settings.GAME_MODE = old_mode
        settings.ENABLE_LLM_NARRATION = old_narration

    assert action["action"] == "look"
    assert tracking_llm.calls == 1
    assert "shadowed corner" in narrative.lower()


@pytest.mark.asyncio
async def test_move_narration_uses_destination_room_context_and_boosts_copy(game_engine_with_state):
    old_mode = settings.GAME_MODE
    old_narration = settings.ENABLE_LLM_NARRATION
    settings.GAME_MODE = "programmatic"
    settings.ENABLE_LLM_NARRATION = True

    llm = _NarrationEchoLLMService()
    try:
        narrative, action = await game_engine_with_state.process_turn("go north", llm)
    finally:
        settings.GAME_MODE = old_mode
        settings.ENABLE_LLM_NARRATION = old_narration

    assert action["action"] == "move"
    assert "current room snapshot: you are in the northern room" in llm.last_prompt.lower()
    assert "resolved action type: move" in llm.last_prompt.lower()
    assert "faint echo from beyond the nearest passage" in narrative.lower()


@pytest.mark.asyncio
async def test_init_game_force_new_bypasses_existing_save(tmp_path, monkeypatch):
    engine = GameEngine(save_path=str(tmp_path / "savegame.json"))
    calls = {"load": 0, "generate": 0}

    def fake_load_game(_path: str):
        calls["load"] += 1
        return GameState(
            theme="loaded-theme",
            player=PlayerState(current_room_id="room_0"),
            rooms={"room_0": Room(id="room_0", is_generated=True)},
        )

    async def fake_initial_generation(_llm, strict_llm: bool = False):
        calls["generate"] += 1
        return GameState(
            theme="generated-theme",
            player=PlayerState(current_room_id="room_0"),
            rooms={"room_0": Room(id="room_0", is_generated=True)},
        )

    monkeypatch.setattr(game_module, "load_game", fake_load_game)
    monkeypatch.setattr(game_module, "initial_generation", fake_initial_generation)

    await engine.init_game(None, force_new=True)

    assert calls["load"] == 0
    assert calls["generate"] == 1
    assert engine.state is not None
    assert engine.state.theme == "generated-theme"


@pytest.mark.asyncio
async def test_init_game_llm_mode_does_not_silently_fallback_on_generation_failure(tmp_path, monkeypatch):
    engine = GameEngine(save_path=str(tmp_path / "savegame.json"))
    old_mode = settings.GAME_MODE
    settings.GAME_MODE = "llm"

    async def failing_initial_generation(_llm, strict_llm: bool = False):
        raise RuntimeError("llm unavailable")

    monkeypatch.setattr(game_module, "initial_generation", failing_initial_generation)

    class _StubLLM:
        pass

    try:
        with pytest.raises(RuntimeError, match="GAME_MODE=llm"):
            await engine.init_game(cast(LLMService, _StubLLM()), force_new=True)
    finally:
        settings.GAME_MODE = old_mode
