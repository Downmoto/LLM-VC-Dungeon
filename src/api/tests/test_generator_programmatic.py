import pytest

from app.game.generator import expand_room, generate_theme
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
    assert "passages lead" in room.description.lower()


@pytest.mark.asyncio
async def test_expand_room_programmatic_difficulty_scales_enemy_hp():
    room = Room(id="room_9", exits={"west": "room_8"})

    await expand_room(room, "a volcanic fortress with cracked basalt halls", None)

    for enemy in room.enemies:
        assert enemy.hp >= 16
        assert enemy.max_hp == enemy.hp
