from validators.composition_validator import validate_composition


def test_model_weather_replaces_global_fallback_weather():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "fallback-weather",
                    "type": "widget",
                    "role": "weather",
                    "source": "fallback",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 96,
                },
                {
                    "id": "weather-card",
                    "type": "glassCard",
                    "role": "weather",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                },
            ]
        }
    )

    assert [layer["id"] for layer in result["dsl"]["layers"]] == [
        "weather-card"
    ]


def test_duplicate_time_keeps_higher_priority_source():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "repair-time",
                    "type": "text",
                    "role": "time",
                    "source": "repair",
                    "content": "09:27",
                    "x": 195,
                    "y": 160,
                },
                {
                    "id": "model-time",
                    "type": "text",
                    "role": "time",
                    "source": "model",
                    "content": "06:30",
                    "x": 195,
                    "y": 180,
                },
            ]
        }
    )

    times = [
        layer for layer in result["dsl"]["layers"]
        if layer.get("role") == "time"
    ]
    assert len(times) == 1
    assert times[0]["id"] == "model-time"


def test_semantic_role_aliases_are_normalized_before_deduplication():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "clock",
                    "type": "text",
                    "role": "clock",
                    "source": "model",
                    "content": "06:30",
                    "x": 195,
                    "y": 160,
                },
                {
                    "id": "repair-time",
                    "type": "text",
                    "role": "time",
                    "source": "repair",
                    "content": "09:27",
                    "x": 195,
                    "y": 180,
                },
            ]
        }
    )

    times = [
        layer for layer in result["dsl"]["layers"]
        if layer.get("role") == "time"
    ]
    assert len(times) == 1
    assert times[0]["id"] == "clock"


def test_card_group_removes_independent_duplicate_weather():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "weather-card",
                    "type": "glassCard",
                    "role": "weather",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                },
                {
                    "id": "schedule-card",
                    "type": "glassCard",
                    "role": "schedule",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                },
                {
                    "id": "quote-card",
                    "type": "glassCard",
                    "role": "quote",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                },
                {
                    "id": "repair-weather",
                    "type": "widget",
                    "role": "weather",
                    "source": "repair",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 96,
                },
            ],
            "cardGroups": [
                {
                    "id": "bottom-cards",
                    "cardIds": [
                        "weather-card",
                        "schedule-card",
                        "quote-card",
                    ],
                    "activeIndex": 0,
                }
            ],
        }
    )

    assert "repair-weather" not in {
        layer["id"] for layer in result["dsl"]["layers"]
    }
    assert result["dsl"]["cardGroups"][0]["cardIds"] == [
        "weather-card",
        "schedule-card",
        "quote-card",
    ]


def test_card_roles_are_inferred_from_ids_before_repair_duplicates_are_kept():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "card-weather",
                    "type": "glassCard",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                    "content": {"title": "Weather"},
                },
                {
                    "id": "card-schedule",
                    "type": "glassCard",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                    "content": {"title": "Schedule"},
                },
                {
                    "id": "card-music",
                    "type": "glassCard",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                    "content": {"title": "Music"},
                },
                {
                    "id": "repair-weather",
                    "type": "widget",
                    "role": "weather",
                    "source": "repair",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 96,
                },
            ],
            "cardGroups": [
                {
                    "id": "bottom-cards",
                    "cardIds": [
                        "card-weather",
                        "card-schedule",
                        "card-music",
                    ],
                }
            ],
        }
    )

    layers = result["dsl"]["layers"]
    assert "repair-weather" not in {layer["id"] for layer in layers}
    assert {
        layer["id"]: layer.get("role") for layer in layers
    } == {
        "card-weather": "weather",
        "card-schedule": "schedule",
        "card-music": "music",
    }
    assert len(result["dsl"]["cardGroups"][0]["cardIds"]) == 3


def test_explicit_no_weather_removes_an_unrequested_weather_card():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "title",
                    "type": "text",
                    "content": "Morning",
                    "x": 195,
                    "y": 160,
                },
                {
                    "id": "weather",
                    "type": "widget",
                    "role": "weather",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 96,
                },
            ]
        },
        "Do not add a weather card.",
    )

    assert "weather" not in {
        layer.get("role") for layer in result["dsl"]["layers"]
    }


def test_card_group_adopts_missing_card_role_in_owned_region():
    result = validate_composition(
        {
            "layers": [
                {
                    "id": "schedule-card",
                    "type": "glassCard",
                    "role": "schedule",
                    "source": "model",
                    "x": 25,
                    "y": 660,
                    "width": 340,
                    "height": 110,
                },
                {
                    "id": "repair-weather",
                    "type": "widget",
                    "role": "weather",
                    "source": "repair",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 96,
                },
            ],
            "cardGroups": [
                {
                    "id": "bottom-cards",
                    "cardIds": ["schedule-card"],
                    "activeIndex": 0,
                }
            ],
        }
    )

    assert result["dsl"]["cardGroups"][0]["cardIds"] == [
        "schedule-card",
        "repair-weather",
    ]
