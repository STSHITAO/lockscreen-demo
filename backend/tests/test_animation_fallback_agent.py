from agents.animation_fallback_agent import apply_animation_fallbacks


BASE_DSL = {
    "version": "1.0",
    "canvas": {"width": 390, "height": 844},
    "theme": "night",
    "mode": "static",
    "background": {"type": "color", "value": "#020617"},
    "layers": [],
}


def test_cloud_drift_creates_simple_shape_animation():
    result = apply_animation_fallbacks(
        BASE_DSL,
        "clouds drifting to the right",
        {
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
        },
    )

    cloud = result["dsl"]["layers"][0]
    assert cloud["shape"] == "cloud"
    assert cloud["animation"] == "drift-right"
    assert cloud["fallbackReason"] == "animation_asset_missing"
    assert result["applied"][0]["target"] == "cloud"
    assert result["notices"] == []


def test_heart_beat_attaches_animation_to_existing_layer():
    dsl = {
        **BASE_DSL,
        "layers": [
            {
                "id": "pink-heart",
                "type": "shape",
                "shape": "heart",
                "target": "heart",
                "x": 300,
                "y": 80,
                "width": 50,
                "height": 46,
            }
        ],
    }

    result = apply_animation_fallbacks(
        dsl,
        "\u7231\u5fc3\u8df3\u52a8",
        {
            "intent": {
                "animationRequirements": [
                    {
                        "target": "heart",
                        "motion": "pulse",
                        "complexity": "simple",
                    }
                ]
            }
        },
    )

    assert result["dsl"]["layers"][0]["animation"] == "pulse"
    assert result["dsl"]["mode"] == "dynamic"
    assert result["notices"] == []


def test_complex_animation_returns_notice_without_drawing():
    result = apply_animation_fallbacks(
        BASE_DSL,
        "\u57ce\u5821\u53d8\u6210\u98de\u9f99\u5e76\u98de\u8d70",
        {
            "intent": {
                "animationRequirements": [
                    {
                        "target": "castle",
                        "motion": "transform-and-fly",
                        "complexity": "complex",
                    }
                ]
            }
        },
    )

    assert result["dsl"]["layers"] == []
    assert result["applied"] == []
    assert result["notices"][0]["type"] == "animation_unavailable"
    assert "\u8f83\u590d\u6742" in result["notices"][0]["message"]


def test_descriptive_cloud_target_reuses_existing_layer():
    dsl = {
        **BASE_DSL,
        "layers": [
            {
                "id": "cloud-drift",
                "type": "asset",
                "assetId": "doodle-122",
                "x": 28,
                "y": 90,
                "width": 96,
                "height": 64,
            }
        ],
    }

    result = apply_animation_fallbacks(
        dsl,
        "\u4e91\u6735\u5411\u53f3\u98d8\u52a8",
        {
            "intent": {
                "animationRequirements": [
                    {
                        "target": "drifting clouds",
                        "motion": "drift-right",
                        "complexity": "simple",
                    }
                ]
            }
        },
    )

    layers = result["dsl"]["layers"]
    assert len(layers) == 1
    assert layers[0]["id"] == "cloud-drift"
    assert layers[0]["animation"] == "drift-right"
    assert layers[0].get("fallback") is not True


def test_frame_sequence_candidate_is_preferred_for_twinkling_star():
    result = apply_animation_fallbacks(
        BASE_DSL,
        "\u661f\u661f\u6301\u7eed\u95ea\u70c1",
        {
            "intent": {
                "animationRequirements": [
                    {
                        "target": "twinkling stars",
                        "motion": "twinkle",
                        "complexity": "simple",
                        "preferredPosition": "top-right",
                    }
                ]
            },
            "materialCandidateGroups": [
                {
                    "slot": "decoration",
                    "requirement": {
                        "subjects": ["star"],
                        "query": "star twinkle",
                    },
                    "candidates": [
                        {
                            "assetId": "frame-star-twinkle-001",
                            "assetType": "frameSequence",
                        }
                    ],
                }
            ],
        },
    )

    animation = next(
        layer
        for layer in result["dsl"]["layers"]
        if layer.get("type") == "frameAnimation"
    )
    assert animation["assetId"] == "frame-star-twinkle-001"
    assert len(animation["frames"]) == 5
    assert result["dsl"]["mode"] == "dynamic"
    assert result["notices"] == []
