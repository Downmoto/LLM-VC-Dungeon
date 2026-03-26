import pytest
from types import SimpleNamespace

from app.game.intent import classify_intent_programmatic
from app.services import llm as llm_module
from app.services.llm import LLMService


def test_classify_move_with_direction_word():
    intent = classify_intent_programmatic("go north")
    assert intent == {"action": "move", "direction": "north"}


def test_classify_take_with_target_extraction():
    intent = classify_intent_programmatic("pick up the silver key")
    assert intent["action"] == "take"
    assert intent["target"] == "silver key"


def test_classify_take_with_conversational_prefix():
    intent = classify_intent_programmatic("i grab the coal tonic")
    assert intent["action"] == "take"
    assert intent["target"] == "coal tonic"


def test_classify_attack_with_target_extraction():
    intent = classify_intent_programmatic("attack the cave rat")
    assert intent["action"] == "attack"
    assert intent["target"] == "cave rat"


def test_classify_attack_with_gerund_form():
    intent = classify_intent_programmatic("attacking the forest wraith")
    assert intent["action"] == "attack"
    assert intent["target"] == "forest wraith"


def test_classify_inventory():
    intent = classify_intent_programmatic("show inventory")
    assert intent == {"action": "inventory"}


def test_classify_health_status():
    intent = classify_intent_programmatic("how much health do i have")
    assert intent == {"action": "health"}


def test_classify_unknown_for_non_action_input():
    intent = classify_intent_programmatic("sing a lullaby")
    assert intent == {"action": "unknown"}


def test_classify_where_am_i_as_look():
    intent = classify_intent_programmatic("where am i")
    assert intent == {"action": "look"}


def test_classify_general_question_as_query():
    intent = classify_intent_programmatic("how large is the chest?")
    assert intent["action"] == "query"
    assert "chest" in intent["target"]


@pytest.mark.asyncio
async def test_llm_classify_intent_returns_unknown_after_tool_call_failures(monkeypatch):
    service = object.__new__(LLMService)

    class _StubAgent:
        def __init__(self):
            self.calls = 0

        async def ainvoke(self, _prompt: str):
            self.calls += 1
            return SimpleNamespace(tool_calls=[])

    async def _no_sleep(_seconds: float):
        return None

    service.classify_agent = _StubAgent()
    monkeypatch.setattr(llm_module.asyncio, "sleep", _no_sleep)

    result = await service.classify_intent("go north", history_context="recent turns")

    assert result == {"action": "unknown"}
    assert service.classify_agent.calls == 3


@pytest.mark.asyncio
async def test_llm_classify_intent_ignores_unknown_tool_and_falls_back(monkeypatch):
    service = object.__new__(LLMService)

    responses = [
        SimpleNamespace(tool_calls=[{"name": "not_a_real_tool", "args": {}}]),
        SimpleNamespace(tool_calls=[]),
        SimpleNamespace(tool_calls=[]),
    ]

    class _StubAgent:
        def __init__(self):
            self.calls = 0

        async def ainvoke(self, _prompt: str):
            current = responses[self.calls]
            self.calls += 1
            return current

    async def _no_sleep(_seconds: float):
        return None

    service.classify_agent = _StubAgent()
    monkeypatch.setattr(llm_module.asyncio, "sleep", _no_sleep)

    result = await service.classify_intent("attack skeleton")

    assert result == {"action": "unknown"}
    assert service.classify_agent.calls == 3


@pytest.mark.asyncio
async def test_llm_classify_intent_succeeds_on_retry(monkeypatch):
    service = object.__new__(LLMService)

    responses = [
        SimpleNamespace(tool_calls=[]),
        SimpleNamespace(tool_calls=[{"name": "action_move", "args": {"direction": "north"}}]),
    ]

    class _StubAgent:
        def __init__(self):
            self.calls = 0

        async def ainvoke(self, _prompt: str):
            current = responses[self.calls]
            self.calls += 1
            return current

    async def _no_sleep(_seconds: float):
        return None

    service.classify_agent = _StubAgent()
    monkeypatch.setattr(llm_module.asyncio, "sleep", _no_sleep)

    result = await service.classify_intent("go north")

    assert result == {"action": "move", "direction": "north"}
    assert service.classify_agent.calls == 2
