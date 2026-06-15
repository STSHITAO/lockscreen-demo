from agents.compound_draw_agent import create_compound_layer
import pytest


def test_compound_draw_agent_clamps_parts_and_budget():
    layer = create_compound_layer(
        "orange cat",
        "center",
        "cute",
        {"width": 390, "height": 844},
        planner=lambda request: {
            "width": 180,
            "height": 190,
            "parts": [
                {
                    "shape": "ellipse",
                    "x": -1,
                    "y": 0.1,
                    "width": 2,
                    "height": 0.5,
                    "fill": "#f97316",
                }
                for _ in range(30)
            ],
        },
    )

    assert layer["type"] == "compoundShape"
    assert layer["source"] == "draw-agent"
    assert len(layer["parts"]) == 24
    assert layer["parts"][0]["x"] == 0
    assert layer["parts"][0]["width"] == 1


def test_compound_draw_agent_supports_polygon_and_line_parts():
    layer = create_compound_layer(
        "simple sailboat",
        "center",
        "sky",
        {"width": 390, "height": 844},
        planner=lambda request: {
            "parts": [
                {
                    "shape": "polygon",
                    "points": [[0.1, 0.7], [0.9, 0.7], [0.7, 0.95]],
                    "fill": "#0f766e",
                },
                {
                    "shape": "line",
                    "x": 0.5,
                    "y": 0.15,
                    "width": 0,
                    "height": 0.55,
                    "stroke": "#f8fafc",
                    "strokeWidth": 0.03,
                },
            ]
        },
    )

    assert [part["shape"] for part in layer["parts"]] == [
        "polygon",
        "line",
    ]


def test_compound_draw_agent_rejects_invalid_or_free_form_parts():
    with pytest.raises(ValueError):
        create_compound_layer(
            "detailed object",
            "center",
            "custom",
            {"width": 390, "height": 844},
            planner=lambda request: {
                "parts": [
                    {"shape": "path", "d": "M0 0 L10 10"},
                    {"shape": "image", "src": "https://example.com/a.png"},
                ]
            },
        )
