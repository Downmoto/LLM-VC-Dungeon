from fastapi.testclient import TestClient

from app import main
from app.game.game import GameEngine
from app.game.models import GameState, PlayerState, Room


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
