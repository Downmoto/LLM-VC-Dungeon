import pytest
import json

from app.game.generator import expand_room, generate_theme, initial_generation
from app.game.models import Room


@pytest.mark.asyncio
async def test_generate_theme_programmatic_without_llm():
    theme = await generate_theme(None)
    assert isinstance(theme, str)
    assert len(theme) > 10


@pytest.mark.asyncio
async def test_expand_room_programmatic_populates_description_and_flags():
    room = Room(id="room_1", exits={"north": "room_2"})

    await expand_room(room, "an abandoned dwarven mine reclaimed by roots and fungus", None)

    assert room.is_generated is True
    assert room.description
    lowered = room.description.lower()
    assert any(phrase in lowered for phrase in ["passages lead", "routes branch", "openings continue", "corridors stretch"])


@pytest.mark.asyncio
async def test_expand_room_programmatic_difficulty_scales_enemy_hp():
    room = Room(id="room_9", exits={"west": "room_8"})

    await expand_room(room, "a volcanic fortress with cracked basalt halls", None)

    for enemy in room.enemies:
        assert enemy.hp >= 16
        assert enemy.max_hp == enemy.hp


class _SingleCallDungeonLLM:
    def __init__(self):
        self.calls = 0

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        self.calls += 1
        rooms = []
        for i in range(10):
            rooms.append(
                {
                    "id": f"room_{i}",
                    "description": f"room {i} description",
                    "items": [
                        {
                            "name": f"item {i}",
                            "type": "TREASURE",
                            "description": "shiny",
                        }
                    ],
                    "enemies": [],
                }
            )
        return json.dumps({"theme": "clockwork catacombs", "rooms": rooms})


@pytest.mark.asyncio
async def test_initial_generation_llm_uses_single_full_dungeon_request():
    llm = _SingleCallDungeonLLM()

    game_state = await initial_generation(llm)

    assert llm.calls == 1
    assert game_state.theme == "clockwork catacombs"
    assert len(game_state.rooms) == 10
    assert all(room.is_generated for room in game_state.rooms.values())
