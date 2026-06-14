from agents.interaction_agent import apply_interaction_requirements


BASE_DSL = {
    "version": "1.0",
    "canvas": {"width": 390, "height": 844},
    "theme": "cute",
    "mode": "static",
    "background": {"type": "color", "value": "#fb7185"},
    "layers": [],
}


def test_multi_tap_binds_to_existing_heart_layer():
    dsl = {
        **BASE_DSL,
        "layers": [
            {
                "id": "main-heart",
                "type": "shape",
                "shape": "heart",
                "x": 290,
                "y": 80,
                "width": 52,
                "height": 48,
            }
        ],
    }

    result = apply_interaction_requirements(
        dsl,
        "连续点击爱心三次后爆炸",
        {"intent": {"interactionRequirements": []}},
    )

    interaction = result["dsl"]["interactions"][0]
    assert interaction["targetId"] == "main-heart"
    assert interaction["trigger"]["count"] == 3
    assert interaction["actions"][-1]["type"] == "burst"


def test_missing_star_uses_controlled_fallback_layer():
    result = apply_interaction_requirements(
        BASE_DSL,
        "点击星星后爆炸",
        {"intent": {"interactionRequirements": []}},
    )

    star = next(
        layer
        for layer in result["dsl"]["layers"]
        if layer.get("target") == "star"
    )
    interaction = result["dsl"]["interactions"][0]
    assert star["fallback"] is True
    assert interaction["targetId"] == star["id"]


def test_long_press_creates_start_and_release_interactions():
    result = apply_interaction_requirements(
        BASE_DSL,
        "星星长按加速闪烁，松开后爆炸",
        {"intent": {"interactionRequirements": []}},
    )

    trigger_types = {
        interaction["trigger"]["type"]
        for interaction in result["dsl"]["interactions"]
    }
    assert trigger_types == {"longPressStart", "longPressEnd"}


def test_swipe_builds_card_group_from_card_layers():
    dsl = {
        **BASE_DSL,
        "layers": [
            {
                "id": "weather",
                "type": "widget",
                "role": "weather",
                "x": 32,
                "y": 690,
                "width": 326,
                "height": 96,
            },
            {
                "id": "schedule",
                "type": "glassCard",
                "x": 32,
                "y": 690,
                "width": 326,
                "height": 96,
            },
        ],
    }

    result = apply_interaction_requirements(
        dsl,
        "左右滑动切换天气和日程卡片",
        {"intent": {"interactionRequirements": []}},
    )

    group = result["dsl"]["cardGroups"][0]
    assert group["cardIds"] == ["weather", "schedule"]
    assert {
        interaction["trigger"]["type"]
        for interaction in result["dsl"]["interactions"]
    } == {"swipeLeft", "swipeRight"}


def test_swipe_reuses_existing_valid_card_group():
    dsl = {
        **BASE_DSL,
        "layers": [
            {"id": "weather", "type": "widget"},
            {"id": "schedule", "type": "glassCard"},
        ],
        "cardGroups": [
            {
                "id": "info-carousel",
                "cardIds": ["weather", "schedule"],
                "activeIndex": 0,
                "loop": True,
                "transition": "slide",
            }
        ],
    }

    result = apply_interaction_requirements(
        dsl,
        "左右滑动切换天气和日程卡片",
        {"intent": {"interactionRequirements": []}},
    )

    assert len(result["dsl"]["cardGroups"]) == 1
    assert {
        interaction["targetId"]
        for interaction in result["dsl"]["interactions"]
    } == {"info-carousel"}


def test_explicit_requirement_updates_existing_model_interaction():
    dsl = {
        **BASE_DSL,
        "layers": [
            {
                "id": "main-heart",
                "type": "shape",
                "shape": "heart",
                "x": 290,
                "y": 80,
                "width": 52,
                "height": 48,
            }
        ],
        "interactions": [
            {
                "id": "model-heart-tap",
                "targetId": "main-heart",
                "trigger": {
                    "type": "multiTap",
                    "count": 3,
                    "withinMs": 1200,
                },
                "actions": [{"type": "reset"}],
            }
        ],
    }
    context = {
        "intent": {
            "interactionRequirements": [
                {
                    "target": "heart",
                    "trigger": {
                        "type": "multiTap",
                        "count": 5,
                        "withinMs": 1500,
                    },
                    "actions": [
                        {"type": "animate", "animation": "pulse"},
                        {"type": "burst", "afterEffect": "restore"},
                    ],
                }
            ]
        }
    }

    result = apply_interaction_requirements(
        dsl,
        "连续点击爱心五次后爆炸",
        context,
    )

    interactions = result["dsl"]["interactions"]
    assert len(interactions) == 1
    assert interactions[0]["trigger"]["count"] == 5
    assert [action["type"] for action in interactions[0]["actions"]] == [
        "animate",
        "burst",
    ]
