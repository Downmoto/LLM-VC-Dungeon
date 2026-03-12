from app.game.intent import classify_intent_programmatic


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


def test_classify_inventory():
    intent = classify_intent_programmatic("show inventory")
    assert intent == {"action": "inventory"}


def test_classify_unknown_for_non_action_input():
    intent = classify_intent_programmatic("sing a lullaby")
    assert intent == {"action": "unknown"}


def test_classify_where_am_i_as_look():
    intent = classify_intent_programmatic("where am i")
    assert intent == {"action": "look"}
