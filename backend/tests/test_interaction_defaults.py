from utils.interaction_defaults import (
    normalize_interaction_requirements,
    normalize_trigger,
)


def test_explicit_multi_tap_count_is_preserved():
    requirements = normalize_interaction_requirements(
        None,
        "连续点击爱心五次，爱心加速跳动然后爆炸",
    )

    requirement = requirements[0]
    assert requirement["target"] == "heart"
    assert requirement["trigger"] == {
        "type": "multiTap",
        "count": 5,
        "withinMs": 1500,
    }
    assert [action["type"] for action in requirement["actions"]] == [
        "animate",
        "burst",
    ]


def test_ambiguous_multi_tap_defaults_to_three():
    requirements = normalize_interaction_requirements(
        None,
        "连续点击爱心几次后爆炸",
    )

    assert requirements[0]["trigger"]["count"] == 3


def test_long_press_creates_start_and_release_actions():
    requirements = normalize_interaction_requirements(
        None,
        "星星长按加速闪烁，松开后爆炸",
    )

    requirement = requirements[0]
    assert requirement["target"] == "star"
    assert requirement["trigger"] == {
        "type": "longPressStart",
        "durationMs": 500,
    }
    assert requirement["actions"][0]["until"] == "release"
    assert requirement["releaseActions"][0]["type"] == "stopAnimation"
    assert requirement["releaseActions"][1]["type"] == "burst"


def test_interaction_values_are_clamped():
    requirements = normalize_interaction_requirements(
        [
            {
                "target": "heart",
                "trigger": {
                    "type": "multiTap",
                    "count": 99,
                    "withinMs": 50,
                },
                "actions": [
                    {
                        "type": "burst",
                        "count": 200,
                        "duration": 99999,
                        "afterEffect": "restore",
                    }
                ],
            }
        ],
        "",
    )

    requirement = requirements[0]
    assert requirement["trigger"]["count"] == 10
    assert requirement["trigger"]["withinMs"] == 300
    assert requirement["actions"][0]["count"] == 40
    assert requirement["actions"][0]["duration"] == 5000


def test_controlled_actions_override_model_complexity_label():
    requirements = normalize_interaction_requirements(
        [
            {
                "target": "heart",
                "trigger": {"type": "multiTap", "count": 5},
                "actions": [
                    {"type": "animate", "animation": "pulse"},
                    {"type": "burst", "afterEffect": "hide"},
                ],
                "complexity": "complex",
            }
        ],
        "",
    )

    assert requirements[0]["complexity"] == "simple"


def test_card_group_alias_is_normalized():
    requirements = normalize_interaction_requirements(
        [
            {
                "target": "bottom card group",
                "trigger": {"type": "swipeLeft"},
                "actions": [
                    {"type": "switchCard", "direction": "next"}
                ],
            }
        ],
        "",
    )

    assert requirements[0]["target"] == "card-group"


def test_bottom_cards_alias_is_normalized():
    requirements = normalize_interaction_requirements(
        [
            {
                "target": "bottom cards",
                "trigger": {"type": "swipeLeft"},
                "actions": [
                    {"type": "switchCard", "direction": "next"}
                ],
            }
        ],
        "",
    )

    assert requirements[0]["target"] == "card-group"


def test_plain_string_trigger_is_accepted():
    assert normalize_trigger("multiTap") == {
        "type": "multiTap",
        "count": 3,
        "withinMs": 1200,
    }


def test_explicit_prompt_count_overrides_model_default():
    requirements = normalize_interaction_requirements(
        [
            {
                "target": "heart",
                "trigger": {
                    "type": "multiTap",
                    "count": 3,
                    "withinMs": 1200,
                },
                "actions": [{"type": "burst"}],
            }
        ],
        "连续点击爱心五次后爆炸",
    )

    assert requirements[0]["trigger"]["count"] == 5
    assert requirements[0]["trigger"]["withinMs"] == 1500
