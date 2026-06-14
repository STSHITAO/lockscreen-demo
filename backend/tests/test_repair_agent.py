from agents import repair_agent
from agents.repair_agent import repair_dsl


def test_repair_agent_adds_missing_weather_without_calling_llm():
    requester_called = False

    def requester(*args, **kwargs):
        nonlocal requester_called
        requester_called = True
        raise AssertionError("deterministic repair should not call the LLM")

    repaired = repair_dsl(
        "底部显示天气卡片",
        {
            "canvas": {"width": 390, "height": 844},
            "background": {"type": "color", "value": "#020617"},
            "layers": [],
        },
        [
            {
                "type": "semantic_missing",
                "level": "error",
                "target": "weather",
                "message": "missing weather",
            }
        ],
        {"requester": requester},
    )

    weather = next(layer for layer in repaired["layers"] if layer.get("role") == "weather")
    assert weather["y"] >= 620
    assert requester_called is False


def test_repair_agent_moves_requested_layer_to_top_left():
    repaired = repair_dsl(
        "月亮放在左上角",
        {
            "canvas": {"width": 390, "height": 844},
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
        },
        [
            {
                "type": "position_mismatch",
                "level": "error",
                "target": "moon",
                "layerId": "moon",
                "expected": "top-left",
                "actual": "top-right",
                "message": "wrong position",
            }
        ],
        {},
    )

    moon = repaired["layers"][0]
    assert moon["x"] < 130
    assert moon["y"] < 220


def test_llm_repair_cannot_delete_existing_valid_layers(monkeypatch):
    original = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "background": {"type": "color", "value": "#020617"},
        "layers": [
            {
                "id": "title",
                "type": "text",
                "content": "Dream",
                "x": 195,
                "y": 180,
            },
            {
                "id": "fallback_cloud",
                "type": "shape",
                "shape": "cloud",
                "x": 24,
                "y": 80,
                "width": 88,
                "height": 52,
                "animation": "drift-right",
            },
        ],
    }

    monkeypatch.setattr(
        repair_agent,
        "_llm_repair",
        lambda *args, **kwargs: {
            **original,
            "layers": [original["layers"][0]],
        },
    )

    repaired = repair_dsl(
        "云朵向右飘动并带有闪光",
        original,
        [
            {
                "type": "semantic_missing",
                "level": "error",
                "target": "sparkle",
                "message": "missing sparkle",
            }
        ],
        {},
    )

    assert {layer["id"] for layer in repaired["layers"]} == {
        "title",
        "fallback_cloud",
    }
