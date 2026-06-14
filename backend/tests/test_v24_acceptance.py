from orchestrator import generate_lockscreen_with_agent_loop


def _base_dsl(layers):
    return {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "cute",
        "background": {
            "type": "gradient",
            "value": "linear-gradient(180deg, #f9a8d4 0%, #db2777 100%)",
        },
        "layers": layers,
    }


def test_five_heart_taps_burst_and_hide():
    draft = _base_dsl(
        [
            {
                "id": "main-heart",
                "type": "shape",
                "shape": "heart",
                "x": 290,
                "y": 80,
                "width": 52,
                "height": 48,
            }
        ]
    )

    result = generate_lockscreen_with_agent_loop(
        "连续点击爱心五次，爱心加速跳动然后爆炸消失",
        draft_generator=lambda prompt: {
            "dsl": draft,
            "context": {"intent": {"interactionRequirements": []}},
        },
    )

    interaction = result["interactions"][0]
    assert interaction["trigger"]["count"] == 5
    assert interaction["actions"][-1]["type"] == "burst"
    assert interaction["actions"][-1]["afterEffect"] == "hide"
    assert result["_debug"]["usedFallback"] is False


def test_star_hold_accelerates_and_release_bursts():
    draft = _base_dsl(
        [
            {
                "id": "main-star",
                "type": "shape",
                "shape": "star",
                "x": 290,
                "y": 80,
                "width": 42,
                "height": 42,
            }
        ]
    )

    result = generate_lockscreen_with_agent_loop(
        "星星长按加速闪烁，松开后爆炸",
        draft_generator=lambda prompt: {
            "dsl": draft,
            "context": {"intent": {"interactionRequirements": []}},
        },
    )

    interactions = {
        interaction["trigger"]["type"]: interaction
        for interaction in result["interactions"]
    }
    assert interactions["longPressStart"]["actions"][0]["speed"] == 3
    assert interactions["longPressStart"]["actions"][0]["until"] == "release"
    assert interactions["longPressEnd"]["actions"][0]["type"] == "stopAnimation"
    assert interactions["longPressEnd"]["actions"][1]["type"] == "burst"
    assert result["_debug"]["usedFallback"] is False


def test_swipe_switches_only_internal_cards():
    draft = _base_dsl(
        [
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
            {
                "id": "quote",
                "type": "glassCard",
                "x": 32,
                "y": 690,
                "width": 326,
                "height": 96,
            },
        ]
    )

    result = generate_lockscreen_with_agent_loop(
        "左右滑动切换天气、日程和短句卡片",
        draft_generator=lambda prompt: {
            "dsl": draft,
            "context": {"intent": {"interactionRequirements": []}},
        },
    )

    group = result["cardGroups"][0]
    assert group["cardIds"] == ["weather", "schedule", "quote"]
    assert {
        interaction["trigger"]["type"]
        for interaction in result["interactions"]
    } == {"swipeLeft", "swipeRight"}
    assert result["canvas"] == {"width": 390, "height": 844}
    assert result["_debug"]["usedFallback"] is False
