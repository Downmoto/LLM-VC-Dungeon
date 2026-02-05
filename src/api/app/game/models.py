from enum import Enum
from typing import List, Dict, Union, Optional
from pydantic import BaseModel, Field

class ItemType(str, Enum):
    WEAPON = "weapon"
    POTION = "potion"
    ARMOR = "armor"
    KEY = "key"
    TREASURE = "treasure"
    OTHER = "other"

class EnemyType(str, Enum):
    BEAST = "beast"
    UNDEAD = "undead"
    HUMANOID = "humanoid"
    CONSTRUCT = "construct"
    DEMON = "demon"
    OTHER = "other"

class Entity(BaseModel):
    name: str
    description: str = ""
    is_generated: bool = False

class Item(Entity):
    type: ItemType = ItemType.OTHER

class Enemy(Entity):
    type: EnemyType = EnemyType.OTHER
    hp: int = 10
    max_hp: int = 10

class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

class Room(BaseModel):
    id: str
    exits: Dict[str, str] = Field(default_factory=dict) # Direction value -> RoomID
    description: str = ""
    items: List[Item] = Field(default_factory=list)
    enemies: List[Enemy] = Field(default_factory=list)
    is_visited: bool = False
    is_generated: bool = False

class PlayerState(BaseModel):
    hp: int = 100
    max_hp: int = 100
    inventory: List[Item] = Field(default_factory=list)
    current_room_id: str

class GameState(BaseModel):
    theme: str = "Generic Dungeon"
    player: PlayerState
    rooms: Dict[str, Room] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)
