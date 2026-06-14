from validators.interaction_validator import validate_interactions


def _dsl(interactions, card_groups=None):
    return {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": "cute",
        "background": {"type": "color", "value": "#fb7185"},
        "layers": [
            {
                "id": "heart",
                "type": "shape",
                "shape": "heart",
                "x": 280,
                "y": 80,
                "width": 52,
                "height": 48,
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
        ],
        "cardGroups": card_groups or [],
        "interactions": interactions,
    }


def test_validator_clamps_trigger_and_burst_values():
    result = validate_interactions(
        _dsl(
            [
                {
                    "id": "heart-many-taps",
                    "targetId": "heart",
                    "trigger": {
                        "type": "multiTap",
                        "count": 50,
                        "withinMs": 20,
                    },
                    "actions": [
                        {
                            "type": "burst",
                            "particleSource": {
                                "type": "shape",
                                "shape": "heart",
                            },
                            "count": 100,
                            "duration": 9000,
                            "afterEffect": "restore",
                        }
                    ],
                }
            ]
        ),
        "",
        {},
    )

    interaction = result["dsl"]["interactions"][0]
    assert interaction["trigger"]["count"] == 10
    assert interaction["trigger"]["withinMs"] == 300
    assert interaction["actions"][0]["count"] == 40
    assert interaction["actions"][0]["duration"] == 5000
    assert result["errors"]


def test_validator_removes_missing_target_without_full_dsl_failure():
    result = validate_interactions(
        _dsl(
            [
                {
                    "id": "missing",
                    "targetId": "not-there",
                    "trigger": {"type": "tap"},
                    "actions": [{"type": "reset"}],
                }
            ]
        ),
        "",
        {},
    )

    assert result["dsl"]["interactions"] == []
    assert result["notices"][0]["type"] == "interaction_unavailable"


def test_validator_rejects_untrusted_particle_asset():
    result = validate_interactions(
        _dsl(
            [
                {
                    "id": "asset-burst",
                    "targetId": "heart",
                    "trigger": {"type": "tap"},
                    "actions": [
                        {
                            "type": "burst",
                            "particleSource": {
                                "type": "asset",
                                "assetId": "not-in-catalog",
                            },
                        }
                    ],
                }
            ]
        ),
        "",
        {},
    )

    source = result["dsl"]["interactions"][0]["actions"][0]["particleSource"]
    assert source == {"type": "shape", "shape": "heart"}
    assert result["errors"]


def test_validator_keeps_valid_card_switch():
    result = validate_interactions(
        _dsl(
            [
                {
                    "id": "next-card",
                    "targetId": "info-cards",
                    "trigger": {"type": "swipeLeft"},
                    "actions": [
                        {"type": "switchCard", "direction": "next"}
                    ],
                }
            ],
            [
                {
                    "id": "info-cards",
                    "cardIds": ["weather"],
                    "activeIndex": 0,
                    "loop": True,
                    "transition": "slide",
                }
            ],
        ),
        "",
        {},
    )

    assert result["ok"] is True
    assert result["dsl"]["interactions"][0]["targetId"] == "info-cards"


def test_validator_normalizes_string_trigger():
    result = validate_interactions(
        _dsl(
            [
                {
                    "id": "heart-tap",
                    "targetId": "heart",
                    "trigger": "tap",
                    "actions": [{"type": "reset"}],
                }
            ]
        ),
        "",
        {},
    )

    assert result["dsl"]["interactions"][0]["trigger"] == {"type": "tap"}
    assert result["errors"][0]["type"] == "interaction_trigger_repaired"
    assert result["errors"][0]["level"] == "warning"
    assert result["ok"] is True
