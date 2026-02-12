import random
import json
from typing import List, Dict, Set, Tuple
from .models import Room, Direction, GameState, PlayerState, Item, Enemy, ItemType, EnemyType

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
    prompt = "Invent a unique, creative, and coherent dungeon theme/setting. Describe it in 1-2 sentences."
    theme = await llm_service.generate_text(prompt, system_prompt="You are a creative dungeon master.")
    return theme.strip()

async def expand_room(room: Room, theme: str, llm_service, previous_room_desc: str | None = None):
    if room.is_generated:
        return

    # Create prompt
    prompt = f"""
    Theme: {theme}
    Room ID: {room.id}
    Exits: {', '.join(room.exits.keys())}
    Previous Room Context: {previous_room_desc if previous_room_desc else "None (Start of dungeon)"}
    
    Task:
    1. Write a vivid, atmospheric description of this room (2-3 sentences).
    2. List 0-2 items found here (name, type).
    3. List 0-1 enemies found here (name, type).
    
    Format the output as JSON:
    {{
        "description": "...",
        "items": [ {{"name": "...", "type": "WEAPON/POTION/ARMOR/KEY/TREASURE/OTHER", "description": "..."}} ],
        "enemies": [ {{"name": "...", "type": "BEAST/UNDEAD/HUMANOID/CONSTRUCT/DEMON/OTHER", "description": "..."}} ]
    }}
    """
    
    try:
        response_text = await llm_service.generate_text(prompt, system_prompt="You are a dungeon generator. Output valid JSON only.")
        
        # clean code blocks if present
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        # Find first { and last }
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        data = json.loads(clean_text)
        
        room.description = data.get("description", "A dark, unexplained room.")
        
        for item_data in data.get("items", []):
            try:
                itype = ItemType[item_data.get("type", "OTHER").upper()]
            except:
                itype = ItemType.OTHER
            room.items.append(Item(name=item_data["name"], description=item_data.get("description", ""), type=itype, is_generated=True))
            
        for enemy_data in data.get("enemies", []):
            try:
                etype = EnemyType[enemy_data.get("type", "OTHER").upper()]
            except:
                etype = EnemyType.OTHER
            room.enemies.append(Enemy(name=enemy_data["name"], description=enemy_data.get("description", ""), type=etype, is_generated=True))
            
    except Exception as e:
        print(f"Error parsing room generation: {e}")
        # Fallback
        room.description = f"You are in {room.id}. The shadows are deep here."
    
    room.is_generated = True

async def initial_generation(llm_service) -> GameState:
    rooms = generate_topology(num_rooms=10)
    theme = await generate_theme(llm_service)
    
    start_room_id = "room_0"
    player = PlayerState(current_room_id=start_room_id)
    
    game_state = GameState(
        theme=theme,
        player=player,
        rooms=rooms,
        history=[f"Welcome to the dungeon. Theme: {theme}"]
    )
    
    # Expand start room
    start_room = rooms[start_room_id]
    await expand_room(start_room, theme, llm_service)
    
    # Expand neighbors of start room (eagerly)
    for exit_dir, neighbor_id in start_room.exits.items():
        neighbor = rooms[neighbor_id]
        await expand_room(neighbor, theme, llm_service, previous_room_desc=start_room.description)
        
    return game_state
