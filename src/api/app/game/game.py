import re
import time
import asyncio
from typing import Optional
from fastapi import BackgroundTasks

from app.services.llm import LLMService
from app.core.config import settings
from .models import GameState, Room, Direction
from .storage import save_game, load_game
from .generator import initial_generation, expand_room
from .intent import classify_intent_programmatic

class GameEngine:
    def __init__(self, save_path: str = "data/savegame.json"):
        self.save_path = save_path
        self.state: Optional[GameState] = None
        self._llm_disabled_until: float = 0.0

    async def get_state(self, llm_service: Optional[LLMService]) -> GameState:
        if not self.state:
            await self.init_game(llm_service)
        assert self.state is not None  # guaranteed after init_game
        return self.state

    async def init_game(self, llm_service: Optional[LLMService], force_new: bool = False):
        mode = settings.GAME_MODE.lower()
        strict_llm = mode == "llm"

        if not force_new:
            try:
                # print(f"Loading game from {self.save_path}")
                self.state = load_game(self.save_path)
                return
            except Exception:
                # print("Save not found, generating new game...")
                pass

        try:
            self.state = await initial_generation(llm_service, strict_llm=strict_llm)
        except Exception as exc:
            if llm_service is None:
                raise
            if mode == "llm":
                raise RuntimeError(f"llm world generation failed while GAME_MODE=llm: {exc}") from exc
            self._mark_llm_temporarily_unavailable(exc)
            self.state = await initial_generation(None, strict_llm=False)

        save_game(self.state, self.save_path)

    def _llm_available(self, llm_service: Optional[LLMService]) -> bool:
        return llm_service is not None and time.time() >= self._llm_disabled_until

    def _mark_llm_temporarily_unavailable(self, error: Exception):
        message = str(error)
        delay_seconds = 60.0

        match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", message, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"'retryDelay'\s*:\s*'([0-9]+)s'", message)
        if match:
            delay_seconds = max(delay_seconds, float(match.group(1)))

        if "429" in message or "resource_exhausted" in message.lower() or "quota" in message.lower():
            self._llm_disabled_until = max(self._llm_disabled_until, time.time() + delay_seconds)

    def _normalize_for_compare(self, text: str) -> str:
        lowered = text.lower()
        alnum_spaced = re.sub(r"[^a-z0-9\s]", " ", lowered)
        return re.sub(r"\s+", " ", alnum_spaced).strip()

    def _narrative_needs_boost(self, candidate: str, logic_result: str, room_description: str) -> bool:
        candidate_n = self._normalize_for_compare(candidate)
        logic_n = self._normalize_for_compare(logic_result)
        room_n = self._normalize_for_compare(room_description)
        if not candidate_n:
            return True
        if candidate_n == logic_n or candidate_n == room_n:
            return True
        if logic_n and candidate_n.startswith(logic_n) and len(candidate_n) <= len(logic_n) + 24:
            return True
        return False

    def _boost_narrative(self, base_text: str, room: Room) -> str:
        additions = [
            "A tense hush settles in as you reassess the chamber.",
            "The dungeon answers with a faint echo from beyond the nearest passage.",
            "For a breath, the room feels alive with small, unsettling movement.",
        ]
        seed = sum(ord(ch) for ch in room.id) % len(additions)
        boost = additions[seed]
        clean_base = base_text.strip()
        if clean_base.endswith((".", "!", "?")):
            return f"{clean_base} {boost}"
        return f"{clean_base}. {boost}"

    def _build_narration_prompt(
        self,
        theme: str,
        room_description: str,
        user_action: str,
        logic_result: str,
        action_type: str,
        available_exits: list[str],
        visible_items: list[str],
    ) -> str:
        exits_text = ", ".join(available_exits) if available_exits else "none"
        items_text = ", ".join(visible_items) if visible_items else "none"
        return f"""
            Theme: {theme}
            Current Room Snapshot: {room_description}
            Player Action: {user_action}
            Resolved Action Type: {action_type}
            Game Logic Facts: {logic_result}
            Available Exits: {exits_text}
            Visible Items: {items_text}

            Task: Write 2-4 sentences of narrative prose about this single turn.
            Constraints:
            - preserve the concrete facts in Game Logic Facts.
            - do not copy any full sentence verbatim from Current Room Snapshot or Game Logic Facts.
            - add at least one fresh sensory or atmospheric detail not present in those inputs.
            - keep the response focused on this exact turn only.
            - after the prose, append exactly these two lines in plain text:
              Directions: <comma-separated exits or "none">
              Items: <comma-separated visible item names or "none">
            - the Directions and Items lines must match Available Exits and Visible Items exactly.
            """

    async def _classify_with_llm_timeout(self, user_input: str, llm_service: LLMService) -> dict:
        timeout_seconds = max(1.0, float(settings.LLM_TIMEOUT_SECONDS))
        return await asyncio.wait_for(
            llm_service.classify_intent(user_input),
            timeout=timeout_seconds,
        )

    async def _classify_with_fallback(self, user_input: str, llm_service: Optional[LLMService]) -> dict:
        mode = settings.GAME_MODE.lower()
        programmatic_intent = classify_intent_programmatic(user_input)

        if mode == "llm":
            if not self._llm_available(llm_service):
                raise RuntimeError("llm intent classification unavailable while GAME_MODE=llm")
            try:
                assert llm_service is not None
                return await self._classify_with_llm_timeout(user_input, llm_service)
            except Exception as exc:
                self._mark_llm_temporarily_unavailable(exc)
                raise RuntimeError(f"llm intent classification failed while GAME_MODE=llm: {exc}") from exc

        if mode == "hybrid":
            intent_data = programmatic_intent
            if intent_data.get("action") == "unknown" and self._llm_available(llm_service):
                try:
                    assert llm_service is not None
                    return await self._classify_with_llm_timeout(user_input, llm_service)
                except Exception as exc:
                    self._mark_llm_temporarily_unavailable(exc)
            return intent_data

        return programmatic_intent
            
    async def process_turn(self, user_input: str, llm_service: Optional[LLMService], background_tasks: Optional[BackgroundTasks] = None) -> tuple[str, dict]:
        if not self.state:
            await self.init_game(llm_service)
        
        assert self.state is not None  # guaranteed after init_game
            
        # 1. classify intent
        intent_data = await self._classify_with_fallback(user_input, llm_service)
        
        action_type = intent_data.get("action", "unknown").lower()
        result_text = ""
        
        current_room = self.state.rooms[self.state.player.current_room_id]
        narrative_room = current_room
        
        if action_type == "move":
            direction = intent_data.get("direction", intent_data.get("target", "")).lower()
            if direction in current_room.exits:
                new_room_id = current_room.exits[direction]
                self.state.player.current_room_id = new_room_id
                new_room = self.state.rooms[new_room_id]
                
                result_text = f"You move {direction}. "
                
                # Trigger generation for neighbors
                if background_tasks:
                     mode = settings.GAME_MODE.lower()
                     strict_llm = mode == "llm"
                     if strict_llm and not self._llm_available(llm_service):
                         generation_llm = None
                     else:
                         generation_llm = llm_service if self._llm_available(llm_service) else None
                     for _, neighbor_id in new_room.exits.items():
                         neighbor = self.state.rooms[neighbor_id]
                         if not neighbor.is_generated:
                             background_tasks.add_task(
                                 expand_room,
                                 neighbor,
                                 self.state.theme,
                                 generation_llm,
                                 new_room.description,
                                 strict_llm,
                             )

                result_text += new_room.description
                if new_room.enemies:
                    result_text += " " + " ".join([f"There is a {e.name} here." for e in new_room.enemies])
                if new_room.items:
                    result_text += " " + " ".join([f"You see a {i.name}." for i in new_room.items])
                narrative_room = new_room
                    
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

        # 2. finalize output narrative
        mode = settings.GAME_MODE.lower()
        strict_llm = mode == "llm"
        final_narrative = result_text
        should_use_llm_narration = settings.ENABLE_LLM_NARRATION or strict_llm
        if should_use_llm_narration:
            if not self._llm_available(llm_service):
                if strict_llm:
                    raise RuntimeError("llm narration unavailable while GAME_MODE=llm")
                assert self.state is not None
                self.state.history.append(f"Action: {user_input} | Result: {final_narrative}")
                save_game(self.state, self.save_path)
                return (final_narrative, intent_data)
            narrative_prompt = self._build_narration_prompt(
                theme=self.state.theme,
                room_description=narrative_room.description,
                user_action=user_input,
                logic_result=result_text,
                action_type=action_type,
                available_exits=list(narrative_room.exits.keys()),
                visible_items=[i.name for i in narrative_room.items],
            )
            try:
                assert llm_service is not None
                llm_narrative = await llm_service.generate_text(narrative_prompt)
                final_narrative = llm_narrative.strip() or result_text
                if self._narrative_needs_boost(final_narrative, result_text, narrative_room.description):
                    final_narrative = self._boost_narrative(result_text, narrative_room)
            except Exception as exc:
                self._mark_llm_temporarily_unavailable(exc)
                if strict_llm:
                    raise RuntimeError(f"llm narration failed while GAME_MODE=llm: {exc}") from exc
                final_narrative = result_text
        
        assert self.state is not None  # guaranteed at this point
        self.state.history.append(f"Action: {user_input} | Result: {final_narrative}")
        save_game(self.state, self.save_path)
        
        return (final_narrative, intent_data)
