from copy import deepcopy

from llm_client import FALLBACK_DSL
from orchestrator import generate_lockscreen_with_agent_loop


def test_orchestrator_never_repairs_more_than_two_rounds():
    repair_calls = []

    def draft_generator(prompt):
        return {"layers": []}

    def repairer(prompt, dsl, errors, context):
        repair_calls.append(deepcopy(errors))
        return dsl

    result = generate_lockscreen_with_agent_loop(
        "底部显示天气卡片",
        draft_generator=draft_generator,
        repairer=repairer,
    )

    assert len(repair_calls) == 2
    assert result["_debug"]["loopCount"] == 2
    assert result["_debug"]["usedFallback"] is True


def test_orchestrator_returns_fallback_when_errors_remain():
    result = generate_lockscreen_with_agent_loop(
        "底部显示天气卡片",
        draft_generator=lambda prompt: {"layers": []},
        repairer=lambda prompt, dsl, errors, context: dsl,
    )

    assert result["canvas"] == FALLBACK_DSL["canvas"]
    assert result["background"] == FALLBACK_DSL["background"]
    assert result["_debug"]["errorsAfterRepair"]


def test_orchestrator_returns_repaired_dsl_when_second_validation_passes():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "night",
        "background": {"type": "color", "value": "#020617"},
        "layers": [
            {
                "id": "moon",
                "type": "shape",
                "shape": "circle",
                "x": 290,
                "y": 60,
                "width": 60,
                "height": 60,
            }
        ],
    }

    result = generate_lockscreen_with_agent_loop(
        "月亮放在左上角",
        draft_generator=lambda prompt: draft,
        repairer=lambda prompt, dsl, errors, context: dsl,
    )

    assert result["_debug"]["loopCount"] == 1
    assert result["_debug"]["usedFallback"] is False
    assert result["layers"][0]["x"] < 130


def test_orchestrator_adds_fallback_shape_when_requested_asset_is_missing():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "night",
        "mode": "static",
        "background": {"type": "color", "value": "#020617"},
        "layers": [],
    }
    context = {
        "materialCandidateGroups": [
            {
                "slot": "decoration",
                "requirement": {"subjects": ["moon"], "query": "moon"},
                "candidates": [],
            }
        ]
    }
    repair_calls = []

    result = generate_lockscreen_with_agent_loop(
        "night lockscreen with a moon in the top-left",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
        repairer=lambda prompt, dsl, errors, repair_context: repair_calls.append(
            errors
        ),
    )

    moon = next(
        layer
        for layer in result["layers"]
        if layer.get("id") == "fallback_moon"
    )
    assert moon["shape"] == "crescent"
    assert moon["fallback"] is True
    assert moon["x"] < 130
    assert result["_debug"]["usedFallback"] is False
    assert repair_calls == []


def test_orchestrator_applies_simple_animation_fallback():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "sky",
        "background": {"type": "color", "value": "#38bdf8"},
        "layers": [],
    }
    context = {
        "intent": {
            "animationRequirements": [
                {
                    "target": "cloud",
                    "motion": "drift-right",
                    "complexity": "simple",
                    "preferredPosition": "top-left",
                }
            ]
        }
    }

    result = generate_lockscreen_with_agent_loop(
        "clouds drifting to the right",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
    )

    cloud = next(layer for layer in result["layers"] if layer.get("target") == "cloud")
    assert cloud["animation"] == "drift-right"
    assert result["mode"] == "dynamic"
    assert result["_debug"]["animationNotices"] == []
    assert result["_debug"]["usedFallback"] is False


def test_orchestrator_keeps_lockscreen_when_complex_animation_is_unavailable():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "fantasy",
        "background": {"type": "color", "value": "#312e81"},
        "layers": [
            {
                "id": "title",
                "type": "text",
                "content": "Fantasy",
                "x": 195,
                "y": 180,
            }
        ],
    }
    context = {
        "intent": {
            "animationRequirements": [
                {
                    "target": "castle",
                    "motion": "transform-and-fly",
                    "complexity": "complex",
                }
            ]
        }
    }

    result = generate_lockscreen_with_agent_loop(
        "castle transforms into a dragon and flies away",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
    )

    assert result["layers"][0]["content"] == "Fantasy"
    assert result["_debug"]["usedFallback"] is False
    notice = result["_debug"]["animationNotices"][0]
    assert notice["target"] == "castle"
    assert notice["type"] == "animation_unavailable"


def test_orchestrator_adds_multi_tap_interaction():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "cute",
        "background": {"type": "color", "value": "#fb7185"},
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
    context = {
        "intent": {
            "interactionRequirements": [
                {
                    "target": "heart",
                    "trigger": {
                        "type": "multiTap",
                        "count": 3,
                        "withinMs": 1200,
                    },
                    "actions": [
                        {
                            "type": "burst",
                            "count": 12,
                            "afterEffect": "restore",
                        }
                    ],
                }
            ]
        }
    }

    result = generate_lockscreen_with_agent_loop(
        "连续点击爱心三次后爆炸",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
    )

    interaction = result["interactions"][0]
    assert interaction["targetId"] == "main-heart"
    assert interaction["trigger"]["count"] == 3
    assert result["_debug"]["interactionNotices"] == []
    assert result["_debug"]["usedFallback"] is False


def test_orchestrator_keeps_lockscreen_for_complex_interaction_notice():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "fantasy",
        "background": {"type": "color", "value": "#312e81"},
        "layers": [
            {
                "id": "title",
                "type": "text",
                "content": "Fantasy",
                "x": 195,
                "y": 180,
            }
        ],
    }
    context = {
        "intent": {
            "interactionRequirements": [
                {
                    "target": "castle",
                    "trigger": {"type": "tap"},
                    "actions": [{"type": "reset"}],
                    "complexity": "complex",
                }
            ]
        }
    }

    result = generate_lockscreen_with_agent_loop(
        "点击城堡后进入复杂剧情",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
    )

    assert result["layers"][0]["content"] == "Fantasy"
    assert result["_debug"]["usedFallback"] is False
    assert result["_debug"]["interactionNotices"][0]["target"] == "castle"


def test_orchestrator_removes_invalid_interaction_without_global_fallback():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "cute",
        "background": {"type": "color", "value": "#fb7185"},
        "layers": [
            {
                "id": "title",
                "type": "text",
                "content": "Still usable",
                "x": 195,
                "y": 180,
            }
        ],
        "interactions": [
            {
                "id": "missing-target",
                "targetId": "not-there",
                "trigger": {"type": "tap"},
                "actions": [{"type": "reset"}],
            }
        ],
    }

    result = generate_lockscreen_with_agent_loop(
        "a simple cute lockscreen",
        draft_generator=lambda prompt: draft,
        repairer=lambda prompt, dsl, errors, context: dsl,
    )

    assert result["layers"][0]["content"] == "Still usable"
    assert result["interactions"] == []
    assert result["_debug"]["usedFallback"] is False
    assert result["_debug"]["interactionNotices"][0]["target"] == "not-there"


def test_orchestrator_preserves_renderable_dsl_after_repairs_are_exhausted():
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "night",
        "background": {"type": "color", "value": "#020617"},
        "layers": [
            {
                "id": "title",
                "type": "text",
                "content": "Keep this design",
                "x": 195,
                "y": 180,
            }
        ],
    }

    result = generate_lockscreen_with_agent_loop(
        "night lockscreen with weather",
        draft_generator=lambda prompt: draft,
        repairer=lambda prompt, dsl, errors, context: dsl,
    )

    assert result["layers"][0]["content"] == "Keep this design"
    assert result["_debug"]["usedFallback"] is False
    assert result["_debug"]["errorsAfterRepair"]


def test_orchestrator_builds_card_group_from_bottom_cards_requirement():
    cards = [
        {
            "id": card_id,
            "type": "glassCard",
            "x": 25,
            "y": 660,
            "width": 340,
            "height": 110,
            "content": card_id,
        }
        for card_id in ("weather-card", "schedule-card", "quote-card")
    ]
    draft = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "night",
        "background": {"type": "color", "value": "#020617"},
        "layers": cards,
    }
    context = {
        "intent": {
            "interactionRequirements": [
                {
                    "target": "bottom cards",
                    "trigger": {"type": "swipeLeft"},
                    "actions": [
                        {"type": "switchCard", "direction": "next"}
                    ],
                },
                {
                    "target": "bottom cards",
                    "trigger": {"type": "swipeRight"},
                    "actions": [
                        {"type": "switchCard", "direction": "prev"}
                    ],
                },
            ]
        }
    }

    result = generate_lockscreen_with_agent_loop(
        "swipe the bottom cards left and right",
        draft_generator=lambda prompt: {"dsl": draft, "context": context},
    )

    assert result["_debug"]["usedFallback"] is False
    assert result["cardGroups"][0]["cardIds"] == [
        "weather-card",
        "schedule-card",
        "quote-card",
    ]
    assert {
        interaction["trigger"]["type"]
        for interaction in result["interactions"]
    } == {"swipeLeft", "swipeRight"}
