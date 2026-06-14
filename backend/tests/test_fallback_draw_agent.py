from agents.fallback_draw_agent import create_fallback_layer
from validators.layout_validator import validate_layout


CANVAS = {"width": 390, "height": 844}


def test_moon_top_left_creates_crescent_in_top_left():
    layer = create_fallback_layer("moon", "top-left", "night", CANVAS)

    assert layer["shape"] == "crescent"
    assert layer["x"] < 130
    assert layer["y"] < 220
    assert layer["fallback"] is True
    assert layer["fallbackReason"] == "asset_missing"


def test_chinese_heart_top_right_creates_heart_in_top_right():
    layer = create_fallback_layer(
        "\u7231\u5fc3",
        "top-right",
        "cute",
        CANVAS,
    )

    assert layer["id"] == "fallback_heart"
    assert layer["shape"] == "heart"
    assert layer["x"] > 240
    assert layer["y"] < 220


def test_fallback_layer_passes_layout_validation():
    layer = create_fallback_layer("moon", "top-left", "night", CANVAS)
    result = validate_layout(
        {"canvas": CANVAS, "layers": [layer]},
        "moon in the top-left",
    )

    assert result["ok"] is True
    assert result["errors"] == []


def test_bottom_fallback_stays_above_weather_safe_area():
    layer = create_fallback_layer("cloud", "bottom", "night", CANVAS)

    assert layer["y"] + layer["height"] <= 660

    result = validate_layout(
        {"canvas": CANVAS, "layers": [layer]},
        "cloud at the bottom",
    )
    assert result["ok"] is True
    assert result["errors"] == []


def test_bottom_corner_fallbacks_keep_their_requested_side():
    for hint, x_check in (
        ("bottom-left", lambda x: x < 130),
        ("bottom-right", lambda x: x > 240),
    ):
        layer = create_fallback_layer("cloud", hint, "night", CANVAS)
        result = validate_layout(
            {"canvas": CANVAS, "layers": [layer]},
            f"cloud in the {hint}",
        )

        assert result["ok"] is True
        assert result["errors"] == []
        assert x_check(result["dsl"]["layers"][0]["x"])
        assert result["dsl"]["layers"][0]["y"] + layer["height"] <= 660
