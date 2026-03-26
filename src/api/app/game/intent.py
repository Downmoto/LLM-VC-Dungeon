from __future__ import annotations

import re
from typing import Dict

from .models import Direction

DIRECTION_ALIASES: dict[str, str] = {
    "north": Direction.NORTH.value,
    "n": Direction.NORTH.value,
    "up": Direction.NORTH.value,
    "south": Direction.SOUTH.value,
    "s": Direction.SOUTH.value,
    "down": Direction.SOUTH.value,
    "east": Direction.EAST.value,
    "e": Direction.EAST.value,
    "right": Direction.EAST.value,
    "west": Direction.WEST.value,
    "w": Direction.WEST.value,
    "left": Direction.WEST.value,
}

MOVE_VERBS = {
    "go",
    "move",
    "walk",
    "run",
    "head",
    "travel",
    "enter",
}

LOOK_VERBS = {
    "look",
    "examine",
    "inspect",
    "search",
    "observe",
    "where",
}

QUERY_WORDS = {
    "what",
    "how",
    "which",
    "who",
    "when",
    "why",
    "tell",
    "describe",
    "details",
    "detail",
    "size",
    "large",
    "big",
    "small",
    "weight",
    "color",
    "material",
}

QUESTION_STARTERS = {
    "can",
    "could",
    "would",
    "should",
    "is",
    "are",
    "am",
    "do",
    "does",
    "did",
    "will",
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
}

TAKE_VERBS = {
    "take",
    "grab",
    "pick",
    "collect",
    "loot",
    "get",
}

ATTACK_VERBS = {
    "attack",
    "attacking",
    "fight",
    "fighting",
    "battle",
    "hit",
    "strike",
    "kill",
    "stab",
    "smash",
}

INVENTORY_WORDS = {
    "inventory",
    "inv",
    "items",
    "bag",
    "backpack",
}

HEALTH_WORDS = {
    "health",
    "hp",
    "status",
    "condition",
    "hurt",
    "wounded",
}

STOPWORDS = {
    "i",
    "im",
    "me",
    "please",
    "can",
    "could",
    "would",
    "will",
    "just",
    "wanna",
    "want",
    "the",
    "a",
    "an",
    "to",
    "at",
    "on",
    "in",
    "my",
    "your",
    "that",
    "this",
    "with",
    "from",
    "around",
    "up",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _extract_direction(tokens: list[str]) -> str | None:
    for token in tokens:
        if token in DIRECTION_ALIASES:
            return DIRECTION_ALIASES[token]
    return None


def _extract_target(tokens: list[str], command_words: set[str]) -> str:
    cleaned = [
        token
        for token in tokens
        if token not in command_words and token not in STOPWORDS
    ]
    return " ".join(cleaned).strip()


def _looks_like_question(text: str, tokens: list[str], token_set: set[str]) -> bool:
    if "?" in text:
        return True
    if tokens and tokens[0] in QUESTION_STARTERS:
        return True
    if token_set & QUERY_WORDS:
        return True
    return False


def classify_intent_programmatic(user_input: str) -> Dict[str, str]:
    text = _normalize(user_input)
    if not text:
        return {"action": "unknown"}

    tokens = _tokenize(text)
    token_set = set(tokens)

    direction = _extract_direction(tokens)

    # direct movement commands like "north" or "n"
    if direction and len(tokens) <= 3:
        if any(word in MOVE_VERBS for word in token_set) or len(tokens) == 1:
            return {"action": "move", "direction": direction}

    if token_set & INVENTORY_WORDS:
        return {"action": "inventory"}

    if token_set & HEALTH_WORDS:
        return {"action": "health"}

    # common location query shorthand, e.g. "where am i"
    if "where" in token_set and "am" in token_set and "i" in token_set:
        return {"action": "look"}

    # treat conversational questions as factual queries rather than look narration
    if _looks_like_question(user_input, tokens, token_set):
        return {"action": "query", "target": text}

    if token_set & LOOK_VERBS:
        return {"action": "look"}

    if token_set & MOVE_VERBS and direction:
        return {"action": "move", "direction": direction}

    if token_set & TAKE_VERBS:
        target = _extract_target(tokens, TAKE_VERBS)
        return {"action": "take", "target": target}

    if token_set & ATTACK_VERBS:
        target = _extract_target(tokens, ATTACK_VERBS)
        return {"action": "attack", "target": target}

    return {"action": "unknown"}
