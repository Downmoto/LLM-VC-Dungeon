import random
import json
import asyncio
from typing import Any, List, Dict, Tuple
from .models import Room, Direction, GameState, PlayerState, Item, Enemy, ItemType, EnemyType

LLM_RETRY_ATTEMPTS = 4


async def _sleep_before_retry(attempt: int):
    delay = min(0.5 * (2 ** (attempt - 1)), 3.0)
    await asyncio.sleep(delay)

PROGRAMMATIC_THEMES = [
    "an abandoned dwarven mine reclaimed by roots and fungus",
    "a flooded crypt where echoes carry across stone vaults",
    "a ruined arcane laboratory humming with unstable energy",
    "a volcanic fortress with cracked basalt halls",
]

BIOME_TABLES = {
    "mine": {
        "descriptors": ["narrow", "dusty", "splintered", "ore-streaked"],
        "features": ["collapsed beams", "ore carts", "pickaxe marks", "fractured supports"],
        "items": [
            ("miner's pick", ItemType.WEAPON, "a heavy pick with a worn grip"),
            ("sturdy vest", ItemType.ARMOR, "workwear reinforced with leather plates"),
            ("coal tonic", ItemType.POTION, "a bitter mixture that restores stamina"),
            ("shaft key", ItemType.KEY, "a brass key tagged with a faded number"),
            ("ore satchel", ItemType.TREASURE, "a pouch filled with low-grade silver ore"),
        ],
        "enemies": [
            ("tunnel rat", EnemyType.BEAST, "a giant rat used to darkness"),
            ("mine warden skeleton", EnemyType.UNDEAD, "bones wrapped in rusted chainmail"),
            ("cave scavenger", EnemyType.HUMANOID, "a desperate looter with a lantern"),
        ],
    },
    "crypt": {
        "descriptors": ["cold", "echoing", "mossy", "sepulchral"],
        "features": ["stone sarcophagi", "dripping vaults", "faded epitaphs", "funerary braziers"],
        "items": [
            ("blessed dagger", ItemType.WEAPON, "a short blade etched with warding runes"),
            ("grave shroud", ItemType.ARMOR, "a woven shroud that dampens cold"),
            ("saint's vial", ItemType.POTION, "a luminous draught of restoration"),
            ("catacomb key", ItemType.KEY, "a black iron key crowned with a skull motif"),
            ("reliquary charm", ItemType.TREASURE, "a gold charm from a broken reliquary"),
        ],
        "enemies": [
            ("restless bones", EnemyType.UNDEAD, "an animated pile of clattering bones"),
            ("crypt hound", EnemyType.BEAST, "a pale hound with glowing eyes"),
            ("grave robber", EnemyType.HUMANOID, "a thief looking for relics"),
        ],
    },
    "arcane": {
        "descriptors": ["humming", "charged", "smoky", "glimmering"],
        "features": ["broken sigils", "shattered glassware", "runic circles", "flickering conduits"],
        "items": [
            ("arc spark rod", ItemType.WEAPON, "a focus rod crackling with weak energy"),
            ("insulated mantle", ItemType.ARMOR, "fabric woven with copper thread"),
            ("focus serum", ItemType.POTION, "a sharp tonic that clears the mind"),
            ("glyph key", ItemType.KEY, "a crystalline key attuned to runic locks"),
            ("charged crystal", ItemType.TREASURE, "a palm-sized crystal pulsing with mana"),
        ],
        "enemies": [
            ("rogue apprentice", EnemyType.HUMANOID, "a panicked mage wielding sparks"),
            ("arc sprite", EnemyType.DEMON, "a tiny malicious elemental"),
            ("clockwork sentinel", EnemyType.CONSTRUCT, "a dented automaton sparking at the joints"),
        ],
    },
    "volcanic": {
        "descriptors": ["smoky", "scorched", "sulfurous", "heat-warped"],
        "features": ["basalt pillars", "magma cracks", "ash drifts", "charred banners"],
        "items": [
            ("obsidian blade", ItemType.WEAPON, "a jagged sword forged from volcanic glass"),
            ("ashguard plate", ItemType.ARMOR, "armor treated to resist searing heat"),
            ("ember tonic", ItemType.POTION, "a warming draught that steadies the body"),
            ("forge key", ItemType.KEY, "a blackened key marked with smithing runes"),
            ("molten ruby", ItemType.TREASURE, "a gem that glows from trapped heat"),
        ],
        "enemies": [
            ("lava crawler", EnemyType.BEAST, "a crusted creature that spits embers"),
            ("infernal zealot", EnemyType.HUMANOID, "a fanatic wrapped in flame-marked cloth"),
            ("char sentinel", EnemyType.CONSTRUCT, "a stone guardian with a molten core"),
        ],
    },
}

AMBIENCE_TABLE = {
    "mine": [
        "A metallic tang hangs in the air.",
        "Distant drips echo through the old shafts.",
        "Loose pebbles crunch under each careful step.",
    ],
    "crypt": [
        "Cold moisture beads on the stone walls.",
        "Every sound returns as a restless whisper.",
        "A funereal stillness presses in from every side.",
    ],
    "arcane": [
        "Static prickles along your skin with each breath.",
        "Faint runes pulse and fade in uneven rhythms.",
        "The smell of ozone lingers over shattered glass.",
    ],
    "volcanic": [
        "Heat ripples distort the edges of the room.",
        "Ash settles in slow spirals across the floor.",
        "A sulfurous haze clings to the back of your throat.",
    ],
}

TRANSITION_TABLE = {
    "mine": [
        "A narrow side tunnel disappears into deeper dark.",
        "Loose struts creak as if something shifted nearby.",
        "A stale breeze carries grit from a distant shaft.",
    ],
    "crypt": [
        "Thin rivulets of water thread between old burial stones.",
        "Your footsteps stir dust that has slept for generations.",
        "Somewhere beyond, a hollow knock echoes and then stops.",
    ],
    "arcane": [
        "A faint hum rises and falls like a strained heartbeat.",
        "Residual sparks skip between cracked metal fittings.",
        "Old chalk marks underfoot suggest rushed experiments.",
    ],
    "volcanic": [
        "Heat pulses from unseen vents beneath the floor.",
        "Fine ash drifts down whenever the stone trembles.",
        "A dull rumble lingers behind the walls.",
    ],
}

ROOM_OPENERS = [
    "You step into",
    "You enter",
    "Ahead lies",
    "This passage opens into",
]

EXIT_LEADS = [
    "Passages lead",
    "Routes branch",
    "Openings continue",
    "Corridors stretch",
]

UNCERTAINTY_TAILS = [
    "though the way ahead feels uncertain.",
    "and each route seems to hide its own danger.",
    "while distant sounds make every choice feel risky.",
    "with silence giving no hint of what awaits.",
]


def _describe_exits(room: Room) -> str:
    exits = list(room.exits.keys())
    if not exits:
        return "There are no visible exits."
    if len(exits) == 1:
        return f"{random.choice(EXIT_LEADS)} {exits[0]}, {random.choice(UNCERTAINTY_TAILS)}"
    return f"{random.choice(EXIT_LEADS)} {', '.join(exits)}, {random.choice(UNCERTAINTY_TAILS)}"


def _infer_biome(theme: str) -> str:
    lowered = theme.lower()
    if "mine" in lowered or "dwarven" in lowered:
        return "mine"
    if "crypt" in lowered or "vault" in lowered:
        return "crypt"
    if "arcane" in lowered or "laboratory" in lowered:
        return "arcane"
    if "volcanic" in lowered or "basalt" in lowered or "magma" in lowered:
        return "volcanic"
    return random.choice(list(BIOME_TABLES.keys()))


def _room_difficulty(room_id: str) -> int:
    try:
        _, num = room_id.split("_", 1)
        index = int(num)
    except Exception:
        return 1

    if index <= 2:
        return 1
    if index <= 5:
        return 2
    if index <= 8:
        return 3
    return 4


def _roll_item_count(difficulty: int) -> int:
    if difficulty == 1:
        return 1 if random.random() < 0.55 else 0
    if difficulty == 2:
        return 1 if random.random() < 0.7 else 0
    if difficulty == 3:
        return 1 + (1 if random.random() < 0.25 else 0)
    return 1 + (1 if random.random() < 0.4 else 0)


def _roll_enemy_count(difficulty: int) -> int:
    if difficulty == 1:
        return 1 if random.random() < 0.35 else 0
    if difficulty == 2:
        return 1 if random.random() < 0.5 else 0
    if difficulty == 3:
        return 1 + (1 if random.random() < 0.2 else 0)
    return 1 + (1 if random.random() < 0.35 else 0)

# Topology Generator
def generate_topology(num_rooms: int) -> Dict[str, Room]:
    rooms: Dict[str, Room] = {}
    
    # Grid based generation: (x, y) -> Room
    grid: Dict[Tuple[int, int], Room] = {}
    
    # Start room
    start_pos: Tuple[int, int] = (0, 0)
    start_room = Room(id="room_0")
    rooms[start_room.id] = start_room
    grid[start_pos] = start_room
    
    created_count = 1
    queue: List[Tuple[int, int]] = [start_pos]
    
    # Simple BFS expansion
    while created_count < num_rooms and queue:
        # Pick random from queue to make it less linear than pure BFS
        idx = random.randint(0, len(queue) - 1)
        current_pos: Tuple[int, int] = queue[idx]
        # Don't remove immediately, allow branching, but maybe remove if too crowded?
        # Let's just standard BFS for now but randomize neighbor order
        # Actually standard BFS is fine.
        current_pos = queue.pop(0) 
        
        current_x, current_y = current_pos
        current_room = grid[current_pos]
        
        # Possible directions
        directions = [
            (Direction.NORTH, (0, 1)),
            (Direction.SOUTH, (0, -1)),
            (Direction.EAST, (1, 0)),
            (Direction.WEST, (-1, 0))
        ]
        random.shuffle(directions)
        
        for dir_enum, (dx, dy) in directions:
            if created_count >= num_rooms:
                break
                
            new_pos = (current_x + dx, current_y + dy)
            
            if new_pos not in grid:
                # Create new room
                new_id = f"room_{created_count}"
                new_room = Room(id=new_id)
                rooms[new_id] = new_room
                grid[new_pos] = new_room
                created_count += 1
                queue.append(new_pos)
            
            # Connect rooms (bi-directional)
            neighbor_room = grid[new_pos]
            
            # Check if connection already exists to avoid overwriting
            if dir_enum.value not in current_room.exits:
                # Link current -> neighbor
                current_room.exits[dir_enum.value] = neighbor_room.id
                
                # Link neighbor -> current (opposite direction)
                opp_dir = _get_opposite_direction(dir_enum)
                neighbor_room.exits[opp_dir.value] = current_room.id

    return rooms

def _get_opposite_direction(direction: Direction) -> Direction:
    if direction == Direction.NORTH: return Direction.SOUTH
    if direction == Direction.SOUTH: return Direction.NORTH
    if direction == Direction.EAST: return Direction.WEST
    if direction == Direction.WEST: return Direction.EAST
    return Direction.NORTH

# LLM Hooks
async def generate_theme(llm_service) -> str:
    if llm_service is None:
        return random.choice(PROGRAMMATIC_THEMES)

    prompt = "Invent a unique, creative, and coherent dungeon theme/setting. Describe it in 1-2 sentences."
    theme = await llm_service.generate_text(prompt, system_prompt="You are a creative dungeon master.")
    return theme.strip()


def _extract_json_object(text: str) -> dict[str, Any]:
    clean_text = text.replace("```json", "").replace("```", "").strip()
    start_idx = clean_text.find("{")
    end_idx = clean_text.rfind("}")
    if start_idx == -1 or end_idx == -1:
        raise ValueError("no json object found in llm response")
    clean_text = clean_text[start_idx:end_idx + 1]
    data = json.loads(clean_text)
    if not isinstance(data, dict):
        raise ValueError("llm response json root must be an object")
    return data


def _to_item_type(raw_type: str | None) -> ItemType:
    try:
        return ItemType[(raw_type or "OTHER").upper()]
    except Exception:
        return ItemType.OTHER


def _to_enemy_type(raw_type: str | None) -> EnemyType:
    try:
        return EnemyType[(raw_type or "OTHER").upper()]
    except Exception:
        return EnemyType.OTHER


def _apply_room_payload(room: Room, room_payload: dict[str, Any], fallback_theme: str):
    room.description = room_payload.get(
        "description",
        f"You are in {room.id}, a chamber of {fallback_theme}."
    )

    room.items = []
    for item_data in room_payload.get("items", []):
        if not isinstance(item_data, dict):
            continue
        name = str(item_data.get("name", "unknown item")).strip()
        if not name:
            name = "unknown item"
        room.items.append(
            Item(
                name=name,
                description=str(item_data.get("description", "")).strip(),
                type=_to_item_type(item_data.get("type")),
                is_generated=True,
            )
        )

    room.enemies = []
    for enemy_data in room_payload.get("enemies", []):
        if not isinstance(enemy_data, dict):
            continue
        name = str(enemy_data.get("name", "unknown foe")).strip()
        if not name:
            name = "unknown foe"
        hp = enemy_data.get("hp", 10)
        try:
            hp = max(1, int(hp))
        except Exception:
            hp = 10
        room.enemies.append(
            Enemy(
                name=name,
                description=str(enemy_data.get("description", "")).strip(),
                type=_to_enemy_type(enemy_data.get("type")),
                hp=hp,
                max_hp=hp,
                is_generated=True,
            )
        )

    room.is_generated = True


async def generate_full_dungeon_single_call(rooms: Dict[str, Room], llm_service) -> str:
    room_skeleton = [
        {
            "id": room.id,
            "exits": room.exits,
        }
        for room in rooms.values()
    ]

    prompt = f"""
    Generate a complete dungeon payload as valid JSON only.

    Requirements:
    - Create one coherent dungeon theme.
    - Fill content for every room listed below.
    - Keep room exits exactly as provided.
        - Make each room description meaningfully distinct from the others.
        - Vary sentence openings, sensory details, and points of interest across rooms.
    - For each room provide:
      - description (2-3 sentences)
      - items (0-2 entries)
      - enemies (0-1 entries)

    Allowed item types: WEAPON, POTION, ARMOR, KEY, TREASURE, OTHER
    Allowed enemy types: BEAST, UNDEAD, HUMANOID, CONSTRUCT, DEMON, OTHER

    Room skeleton:
    {json.dumps(room_skeleton, indent=2)}

    Output format:
    {{
      "theme": "...",
      "rooms": [
        {{
          "id": "room_0",
          "description": "...",
          "items": [{{"name": "...", "type": "...", "description": "..."}}],
          "enemies": [{{"name": "...", "type": "...", "description": "...", "hp": 10}}]
        }}
      ]
    }}
    """

    last_error: Exception | None = None
    for attempt in range(1, LLM_RETRY_ATTEMPTS + 1):
        try:
            response_text = await llm_service.generate_text(
                prompt,
                system_prompt="You are a dungeon generator. Output valid JSON only.",
            )
            data = _extract_json_object(response_text)

            theme = str(data.get("theme", "")).strip() or random.choice(PROGRAMMATIC_THEMES)
            rooms_payload = data.get("rooms", [])
            if not isinstance(rooms_payload, list):
                raise ValueError("rooms payload must be a list")

            payload_by_id: dict[str, dict[str, Any]] = {}
            for room_data in rooms_payload:
                if not isinstance(room_data, dict):
                    continue
                room_id = str(room_data.get("id", "")).strip()
                if room_id:
                    payload_by_id[room_id] = room_data

            missing_rooms = [room_id for room_id in rooms.keys() if room_id not in payload_by_id]
            if missing_rooms:
                raise ValueError(f"rooms payload missing ids: {', '.join(missing_rooms)}")

            for room_id, room in rooms.items():
                room_payload = payload_by_id.get(room_id, {})
                _apply_room_payload(room, room_payload, theme)

            return theme
        except Exception as exc:
            last_error = exc
            if attempt < LLM_RETRY_ATTEMPTS:
                await _sleep_before_retry(attempt)

    assert last_error is not None
    raise RuntimeError(f"single-call dungeon generation failed after {LLM_RETRY_ATTEMPTS} attempts: {last_error}") from last_error

async def expand_room(
    room: Room,
    theme: str,
    llm_service,
    previous_room_desc: str | None = None,
    strict_llm: bool = False,
    retry_attempts: int = LLM_RETRY_ATTEMPTS,
):
    if room.is_generated:
        return

    if llm_service is None:
        if strict_llm:
            raise RuntimeError("llm room generation unavailable while strict_llm is enabled")
        biome = _infer_biome(theme)
        table = BIOME_TABLES[biome]
        difficulty = _room_difficulty(room.id)
        descriptor = random.choice(table["descriptors"])
        feature = random.choice(table["features"])
        ambience = random.choice(AMBIENCE_TABLE[biome])
        transition = random.choice(TRANSITION_TABLE[biome])
        opener = random.choice(ROOM_OPENERS)
        first_sentence = f"{opener} a {descriptor} chamber in {theme}, marked by {feature}."
        if previous_room_desc:
            second_sentence = f"{ambience} {transition}"
        else:
            second_sentence = f"{ambience} The first impression is unsettling and immediate."
        room.description = f"{first_sentence} {second_sentence} {_describe_exits(room)}"

        for _ in range(_roll_item_count(difficulty)):
            item_name, item_type, item_desc = random.choice(table["items"])
            room.items.append(Item(name=item_name, description=item_desc, type=item_type, is_generated=True))
        for _ in range(_roll_enemy_count(difficulty)):
            enemy_name, enemy_type, enemy_desc = random.choice(table["enemies"])
            hp = random.randint(8, 12) + (difficulty * 2)
            room.enemies.append(Enemy(name=enemy_name, description=enemy_desc, type=enemy_type, hp=hp, max_hp=hp, is_generated=True))

        room.is_generated = True
        return

    # Create prompt
    prompt = f"""
    Theme: {theme}
    Room ID: {room.id}
    Exits: {', '.join(room.exits.keys())}
    Previous Room Context: {previous_room_desc if previous_room_desc else "None (Start of dungeon)"}
    
    Task:
    1. Write a vivid, atmospheric description of this room (2-3 sentences).
         - avoid reusing exact phrasing from previous room context.
         - include at least one distinct sensory detail that is unique in wording.
    2. List 0-2 items found here (name, type).
    3. List 0-1 enemies found here (name, type).
    
    Format the output as JSON:
    {{
        "description": "...",
        "items": [ {{"name": "...", "type": "WEAPON/POTION/ARMOR/KEY/TREASURE/OTHER", "description": "..."}} ],
        "enemies": [ {{"name": "...", "type": "BEAST/UNDEAD/HUMANOID/CONSTRUCT/DEMON/OTHER", "description": "..."}} ]
    }}
    """
    
    last_error: Exception | None = None
    for attempt in range(1, max(1, retry_attempts) + 1):
        try:
            response_text = await llm_service.generate_text(prompt, system_prompt="You are a dungeon generator. Output valid JSON only.")
            
            data = _extract_json_object(response_text)
            
            room.description = data.get("description", "A dark, unexplained room.")
            room.items = []
            room.enemies = []
            
            for item_data in data.get("items", []):
                try:
                    itype = _to_item_type(item_data.get("type"))
                except Exception:
                    itype = ItemType.OTHER
                room.items.append(Item(name=item_data["name"], description=item_data.get("description", ""), type=itype, is_generated=True))
                
            for enemy_data in data.get("enemies", []):
                try:
                    etype = _to_enemy_type(enemy_data.get("type"))
                except Exception:
                    etype = EnemyType.OTHER
                room.enemies.append(Enemy(name=enemy_data["name"], description=enemy_data.get("description", ""), type=etype, is_generated=True))

            room.is_generated = True
            return
        except Exception as e:
            last_error = e
            print(f"Error parsing room generation (attempt {attempt}): {e}")
            if attempt < max(1, retry_attempts):
                await _sleep_before_retry(attempt)

    if strict_llm:
        raise RuntimeError(f"llm room generation failed while strict_llm is enabled: {last_error}") from last_error
    room.description = f"You are in {room.id}. The shadows are deep here."
    
    room.is_generated = True

async def initial_generation(llm_service, strict_llm: bool = False) -> GameState:
    rooms = generate_topology(num_rooms=10)
    if llm_service is not None:
        try:
            theme = await generate_full_dungeon_single_call(rooms, llm_service)
        except Exception as e:
            print(f"Error in single-call dungeon generation: {e}")
            if strict_llm:
                try:
                    theme = await generate_theme(llm_service)
                    for room in rooms.values():
                        await expand_room(room, theme, llm_service, strict_llm=True)
                except Exception as fallback_exc:
                    raise RuntimeError(
                        "llm dungeon generation failed while strict_llm is enabled "
                        f"(single-call error: {e}; multi-call error: {fallback_exc})"
                    ) from fallback_exc
            else:
                theme = await generate_theme(None)
                for room in rooms.values():
                    await expand_room(room, theme, None, strict_llm=False)
    else:
        if strict_llm:
            raise RuntimeError("llm dungeon generation unavailable while strict_llm is enabled")
        theme = await generate_theme(None)
        for room in rooms.values():
            await expand_room(room, theme, None, strict_llm=False)
    
    start_room_id = "room_0"
    if start_room_id in rooms:
        rooms[start_room_id].is_visited = True
    player = PlayerState(current_room_id=start_room_id)
    
    game_state = GameState(
        theme=theme,
        player=player,
        rooms=rooms,
        history=[f"Welcome to the dungeon. Theme: {theme}"]
    )
    
    return game_state
