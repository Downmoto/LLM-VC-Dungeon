import re
import time
import asyncio
import random
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

    def _error_text(self, error: Exception) -> str:
        message = str(error).strip()
        if message:
            return message
        return f"{error.__class__.__name__} (empty error message)"

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
        visible_enemies: list[str],
        history_context: str,
    ) -> str:
        exits_text = ", ".join(available_exits) if available_exits else "none"
        items_text = ", ".join(visible_items) if visible_items else "none"
        enemies_text = ", ".join(visible_enemies) if visible_enemies else "none"
        return f"""
            Theme: {theme}
            Recent Adventure Context:
            {history_context}
            Current Room Snapshot: {room_description}
            Player Action: {user_action}
            Resolved Action Type: {action_type}
            Game Logic Facts: {logic_result}
            Available Exits: {exits_text}
            Visible Items: {items_text}
            Visible Enemies: {enemies_text}

            Task: Write 2-4 sentences of narrative prose about this single turn.
            Constraints:
            - preserve the concrete facts in Game Logic Facts.
            - do not copy any full sentence verbatim from Current Room Snapshot or Game Logic Facts.
            - add at least one fresh sensory or atmospheric detail not present in those inputs.
            - if Visible Enemies is not "none", mention at least one enemy by name in the prose.
            - keep the response focused on this exact turn only.
            - after the prose, append exactly these two lines in plain text:
              Directions: <comma-separated exits or "none">
              Items: <comma-separated visible item names or "none">
            - the Directions and Items lines must match Available Exits and Visible Items exactly.
            """

    def _history_context(self) -> str:
        assert self.state is not None
        recent_count = max(1, int(settings.HISTORY_RECENT_TURNS))
        recent_turns = [entry for entry in self.state.history if entry.startswith("Action:")][-recent_count:]
        summary = (self.state.history_summary or "").strip()

        if not recent_turns and not summary:
            return "No prior turns yet."

        lines: list[str] = []
        if summary:
            lines.append(f"Summary: {summary}")
        if recent_turns:
            lines.append("Recent turns:")
            lines.extend(recent_turns)
        return "\n".join(lines)

    def _refresh_history_summary(self):
        assert self.state is not None
        summary_limit = max(120, int(settings.HISTORY_SUMMARY_MAX_CHARS))
        recent_count = max(1, int(settings.HISTORY_RECENT_TURNS))
        action_entries = [entry for entry in self.state.history if entry.startswith("Action:")]

        if not action_entries:
            return

        collapsed = " | ".join(action_entries[:-recent_count]) if len(action_entries) > recent_count else ""
        if not collapsed:
            return

        if len(collapsed) <= summary_limit:
            self.state.history_summary = collapsed
            return

        self.state.history_summary = collapsed[-summary_limit:]

    def history_context(self) -> str:
        if not self.state:
            return "No prior turns yet."
        return self._history_context()

    async def _classify_with_llm_timeout(self, user_input: str, history_context: str, llm_service: LLMService) -> dict:
        timeout_seconds = max(1.0, float(settings.LLM_TIMEOUT_SECONDS))
        classify_method = llm_service.classify_intent

        try:
            classify_coro = classify_method(user_input, history_context=history_context)
        except TypeError:
            classify_coro = classify_method(user_input)

        return await asyncio.wait_for(
            classify_coro,
            timeout=timeout_seconds,
        )

    async def _classify_with_fallback(self, user_input: str, llm_service: Optional[LLMService]) -> dict:
        mode = settings.GAME_MODE.lower()
        programmatic_intent = classify_intent_programmatic(user_input)
        history_context = self._history_context() if self.state else "No prior turns yet."

        if mode == "llm":
            if not self._llm_available(llm_service):
                raise RuntimeError("llm intent classification unavailable while GAME_MODE=llm")
            try:
                assert llm_service is not None
                intent_data = await self._classify_with_llm_timeout(user_input, history_context, llm_service)
                if intent_data.get("action") == "unknown":
                    return programmatic_intent
                return intent_data
            except Exception as exc:
                self._mark_llm_temporarily_unavailable(exc)
                raise RuntimeError(
                    "llm intent classification failed while GAME_MODE=llm: "
                    f"{self._error_text(exc)}"
                ) from exc

        if mode == "hybrid":
            intent_data = programmatic_intent
            if intent_data.get("action") == "unknown" and self._llm_available(llm_service):
                try:
                    assert llm_service is not None
                    llm_intent = await self._classify_with_llm_timeout(user_input, history_context, llm_service)
                    if llm_intent.get("action") != "unknown":
                        return llm_intent
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
                already_visited = new_room.is_visited
                new_room.is_visited = True
                
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

                if already_visited:
                    result_text += f"You return to {new_room.id}. {new_room.description}"
                else:
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
                    if enemy.max_hp <= 10:
                        damage = enemy.hp
                    else:
                        damage = random.randint(4, 12)
                    enemy.hp = max(0, enemy.hp - damage)

                    if enemy.hp <= 0:
                        current_room.enemies.remove(enemy)
                        result_text = f"You defeated the {enemy.name}! You strike it for {damage} damage."
                    else:
                        retaliation = random.randint(2, 8)
                        self.state.player.hp = max(0, self.state.player.hp - retaliation)
                        result_text = (
                            f"You strike the {enemy.name} for {damage} damage. "
                            f"It retaliates for {retaliation} damage. "
                            f"Your hp is now {self.state.player.hp}/{self.state.player.max_hp}."
                        )
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
        player_defeated = self.state.player.hp <= 0
        if player_defeated:
            final_narrative = (
                f"{result_text} You collapse from your wounds. "
                "Your adventure ends here."
            )
        should_use_llm_narration = settings.ENABLE_LLM_NARRATION or strict_llm
        if should_use_llm_narration and not player_defeated:
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
                visible_enemies=[e.name for e in narrative_room.enemies],
                history_context=self._history_context(),
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
                    raise RuntimeError(
                        "llm narration failed while GAME_MODE=llm: "
                        f"{self._error_text(exc)}"
                    ) from exc
                final_narrative = result_text
        
        assert self.state is not None  # guaranteed at this point
        if player_defeated:
            intent_data = {**intent_data, "game_over": True}
        self.state.history.append(f"Action: {user_input} | Result: {final_narrative}")
        self._refresh_history_summary()
        save_game(self.state, self.save_path)
        
        return (final_narrative, intent_data)
