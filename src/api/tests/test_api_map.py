from fastapi.testclient import TestClient

from app import main
from app.game.game import GameEngine
from app.game.models import GameState, PlayerState, Room
from app.core.config import settings


def test_game_map_endpoint_returns_rooms_and_current_room(tmp_path):
    engine = GameEngine(save_path=str(tmp_path / "savegame.json"))
    room_0 = Room(id="room_0", exits={"north": "room_1"}, description="start", is_generated=True)
    room_1 = Room(id="room_1", exits={"south": "room_0"}, description="north room", is_generated=True)
    engine.state = GameState(
        theme="test theme",
        player=PlayerState(current_room_id="room_0"),
        rooms={"room_0": room_0, "room_1": room_1},
    )

    previous_engine = main.game_engine
    main.game_engine = engine
    try:
        client = TestClient(main.app)
        response = client.get("/api/game/map")
    finally:
        main.game_engine = previous_engine

    assert response.status_code == 200
    payload = response.json()
    assert payload["theme"] == "test theme"
    assert payload["current_room_id"] == "room_0"
    assert len(payload["rooms"]) == 2

    by_id = {room["id"]: room for room in payload["rooms"]}
    assert by_id["room_0"]["exits"]["north"] == "room_1"
    assert by_id["room_1"]["exits"]["south"] == "room_0"


def test_load_game_missing_file_returns_404(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    client = TestClient(main.app)

    response = client.post("/api/load-game", json={"save_path": str(missing)})

    assert response.status_code == 404
    assert "save file not found" in response.json()["detail"].lower()


def test_classify_uses_history_context_when_llm_accepts_it(tmp_path):
    class _TrackingLLM:
        def __init__(self):
            self.history = None

        async def classify_intent(self, user_input: str, history_context: str | None = None):
            self.history = history_context
            return {"action": "look"}

    engine = GameEngine(save_path=str(tmp_path / "savegame.json"))
    engine.state = GameState(
        theme="test theme",
        player=PlayerState(current_room_id="room_0"),
        rooms={"room_0": Room(id="room_0", description="start", is_generated=True)},
        history=["Action: look | Result: old turn result"],
        history_summary="brief summary",
    )

    old_engine = main.game_engine
    old_provider = main.llm_provider
    old_mode = settings.GAME_MODE
    tracking = _TrackingLLM()

    main.game_engine = engine
    main.llm_provider = tracking
    settings.GAME_MODE = "llm"
    try:
        client = TestClient(main.app)
        response = client.post("/api/classify", json={"user_input": "look"})
    finally:
        main.game_engine = old_engine
        main.llm_provider = old_provider
        settings.GAME_MODE = old_mode

    assert response.status_code == 200
    assert response.json()["action"] == "look"
    assert tracking.history is not None
    assert "recent turns" in tracking.history.lower()
