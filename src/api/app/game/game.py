from typing import Dict, Any, Optional
from fastapi import BackgroundTasks

from app.services.llm import LLMService
from .models import GameState, Room, Direction
from .storage import save_game, load_game
from .generator import initial_generation, expand_room

class GameEngine:
    def __init__(self, save_path: str = "data/savegame.json"):
        self.save_path = save_path
        self.state: Optional[GameState] = None

    async def get_state(self, llm_service: LLMService) -> GameState:
        if not self.state:
            await self.init_game(llm_service)
        assert self.state is not None  # guaranteed after init_game
        return self.state

    async def init_game(self, llm_service: LLMService):
        try:
            # print(f"Loading game from {self.save_path}")
            self.state = load_game(self.save_path)
        except Exception:
            # print("Save not found, generating new game...")
            self.state = await initial_generation(llm_service)
            save_game(self.state, self.save_path)
            
    async def process_turn(self, user_input: str, llm_service: LLMService, background_tasks: Optional[BackgroundTasks] = None) -> tuple[str, dict]:
        if not self.state:
            await self.init_game(llm_service)
        
        assert self.state is not None  # guaranteed after init_game
            
        # 1. Classify Intent
        intent_data = await llm_service.classify_intent(user_input)
        
        action_type = intent_data.get("action", "unknown").lower()
        result_text = ""
        
        current_room = self.state.rooms[self.state.player.current_room_id]
        
        if action_type == "move":
            direction = intent_data.get("direction", intent_data.get("target", "")).lower()
            if direction in current_room.exits:
                new_room_id = current_room.exits[direction]
                self.state.player.current_room_id = new_room_id
                new_room = self.state.rooms[new_room_id]
                
                result_text = f"You move {direction}. "
                
                # Trigger generation for neighbors
                if background_tasks:
                     for _, neighbor_id in new_room.exits.items():
                         neighbor = self.state.rooms[neighbor_id]
                         if not neighbor.is_generated:
                             background_tasks.add_task(expand_room, neighbor, self.state.theme, llm_service, new_room.description)

                result_text += new_room.description
                if new_room.enemies:
                    result_text += " " + " ".join([f"There is a {e.name} here." for e in new_room.enemies])
                if new_room.items:
                    result_text += " " + " ".join([f"You see a {i.name}." for i in new_room.items])
                    
            else:
                result_text = f"You cannot go {direction}."
                
        elif action_type == "look":
            result_text = current_room.description
            if current_room.enemies:
                result_text += " Enemies: " + ", ".join([e.name for e in current_room.enemies])
            if current_room.items:
                result_text += " Items: " + ", ".join([i.name for i in current_room.items])
                
        elif action_type == "take":
            target = intent_data.get("target", "").lower()
            found = False
            # Check items in room
            for item in current_room.items:
                if target in item.name.lower():
                    self.state.player.inventory.append(item)
                    current_room.items.remove(item)
                    result_text = f"You took the {item.name}."
                    found = True
                    break
            if not found:
                result_text = f"There is no {target} here."

        elif action_type == "attack":
            target = intent_data.get("target", "").lower()
            found = False
            for enemy in current_room.enemies:
                if target in enemy.name.lower():
                    current_room.enemies.remove(enemy)
                    result_text = f"You defeated the {enemy.name}!"
                    found = True
                    break
            if not found:
                result_text = f"There is no {target} here to attack."
                
        elif action_type == "inventory":
            if self.state.player.inventory:
                result_text = "You have: " + ", ".join([i.name for i in self.state.player.inventory])
            else:
                result_text = "Your inventory is empty."
                
        else:
            result_text = "You do that, but nothing happens."

        # Narrate via LLM
        narrative_prompt = f"""
        Theme: {self.state.theme}
        Current Room: {current_room.description}
        Player Action: {user_input}
        Game Logic Result: {result_text}
        
        Task: Describe the outcome of the action narratively. Keep it concise (1-2 sentences).
        """
        
        final_narrative = await llm_service.generate_text(narrative_prompt)
        
        assert self.state is not None  # guaranteed at this point
        self.state.history.append(f"Action: {user_input} | Result: {final_narrative}")
        save_game(self.state, self.save_path)
        
        return (final_narrative, intent_data)
