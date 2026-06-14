from validators.asset_validator import validate_assets
from validators.layout_validator import extract_position_requirements, validate_layout
from validators.schema_validator import validate_schema
from validators.semantic_validator import validate_semantics


def test_schema_validator_adds_missing_canvas_and_defaults():
    result = validate_schema({"layers": []})

    assert result["ok"] is False
    assert result["dsl"]["canvas"] == {"width": 390, "height": 844}
    assert result["dsl"]["version"] == "1.0"
    assert result["dsl"]["background"]["type"] == "gradient"
    assert any(error["field"] == "canvas" for error in result["errors"])


def test_schema_validator_repairs_duplicate_layer_ids():
    result = validate_schema(
        {
            "layers": [
                {"id": "star", "type": "shape", "shape": "star", "x": 10, "y": 20, "width": 10, "height": 10},
                {"id": "star", "type": "shape", "shape": "star", "x": 30, "y": 40, "width": 10, "height": 10},
            ]
        }
    )

    ids = [layer["id"] for layer in result["dsl"]["layers"]]
    assert ids == ["star", "star-2"]
    assert any(error["type"] == "schema_error" and error["field"] == "layers[1].id" for error in result["errors"])


def test_layout_validator_detects_and_repairs_top_left_position_mismatch():
    dsl = {
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
    }

    result = validate_layout(dsl, "月亮放在左上角")

    mismatch = next(error for error in result["errors"] if error["type"] == "position_mismatch")
    assert mismatch["expected"] == "top-left"
    assert mismatch["actual"] == "top-right"
    assert result["dsl"]["layers"][0]["x"] < 130
    assert result["dsl"]["layers"][0]["y"] < 220


def test_layout_validator_repairs_layer_outside_canvas():
    result = validate_layout(
        {
            "canvas": {"width": 390, "height": 844},
            "layers": [
                {
                    "id": "planet",
                    "type": "asset",
                    "assetId": "doodle-091",
                    "x": 370,
                    "y": 820,
                    "width": 120,
                    "height": 120,
                }
            ],
        }
    )

    layer = result["dsl"]["layers"][0]
    assert layer["x"] + layer["width"] <= 390
    assert layer["y"] + layer["height"] <= 844
    assert any(error["type"] == "layout_out_of_bounds" for error in result["errors"])


def test_bottom_requirement_accepts_bottom_left_weather_card():
    result = validate_layout(
        {
            "canvas": {"width": 390, "height": 844},
            "layers": [
                {
                    "id": "weather",
                    "type": "widget",
                    "role": "weather",
                    "x": 32,
                    "y": 690,
                    "width": 326,
                    "height": 104,
                }
            ],
        },
        "底部显示天气卡片",
    )

    assert not any(error["type"] == "position_mismatch" for error in result["errors"])


def test_starry_style_keyword_does_not_inherit_moon_position():
    requirements = extract_position_requirements(
        "生成一个夜晚星空锁屏，月亮放在左上角，星星围绕四周，底部显示天气卡片"
    )

    assert requirements["moon"] == "top-left"
    assert requirements["weather"] == "bottom"
    assert "star" not in requirements


def test_semantic_validator_detects_missing_weather():
    result = validate_semantics(
        {"theme": "night", "background": {"value": "#020617"}, "layers": []},
        "生成夜晚锁屏，底部显示天气卡片",
    )

    assert any(
        error["type"] == "semantic_missing" and error["target"] == "weather"
        for error in result["errors"]
    )


def test_asset_validator_rejects_unknown_asset_id():
    result = validate_assets(
        {
            "layers": [
                {
                    "id": "moon",
                    "type": "asset",
                    "assetId": "invented-moon",
                    "src": "https://example.com/moon.svg",
                }
            ]
        }
    )

    assert any(error["type"] == "asset_missing" for error in result["errors"])
    assert result["dsl"]["layers"] == []


def test_asset_validator_accepts_shape_fallback_for_empty_material_slot():
    result = validate_assets(
        {
            "layers": [
                {
                    "id": "moon",
                    "type": "shape",
                    "shape": "circle",
                    "x": 24,
                    "y": 64,
                    "width": 60,
                    "height": 60,
                }
            ]
        },
        "月亮放在左上角",
        {
            "materialCandidateGroups": [
                {
                    "slot": "decoration",
                    "requirement": {"subjects": ["moon"], "query": "moon"},
                    "candidates": [],
                }
            ]
        },
    )

    assert result["ok"] is True
    assert result["errors"] == []


def test_asset_validator_ignores_optional_empty_slot_not_requested_by_user():
    result = validate_assets(
        {"layers": []},
        "生成夜晚星空锁屏",
        {
            "materialCandidateGroups": [
                {
                    "slot": "decoration",
                    "requirement": {"subjects": ["geometry"], "query": "geometry"},
                    "candidates": [],
                }
            ]
        },
    )

    assert result["ok"] is True
    assert result["errors"] == []


def test_schema_and_asset_validators_accept_trusted_frame_animation():
    dsl = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "background": {"type": "color", "value": "#020617"},
        "layers": [
            {
                "id": "twinkle",
                "type": "frameAnimation",
                "assetId": "frame-star-twinkle-001",
                "frames": ["https://untrusted.example/frame.png"],
                "fps": 99,
                "x": 280,
                "y": 300,
                "width": 80,
                "height": 80,
            }
        ],
    }

    schema_result = validate_schema(dsl)
    asset_result = validate_assets(schema_result["dsl"])
    layer = asset_result["dsl"]["layers"][0]

    assert not any(
        error.get("field") == "layers[0].type"
        for error in schema_result["errors"]
    )
    assert asset_result["ok"] is True
    assert layer["frames"] == [
        f"/materials/frames/star_twinkle/{index:02d}.png"
        for index in range(1, 6)
    ]
    assert layer["fps"] == 6
    assert layer["loop"] is True
    assert layer["poster"].endswith("/03.png")


def test_layout_validator_allows_full_canvas_background_and_thin_lines():
    result = validate_layout(
        {
            "canvas": {"width": 390, "height": 844},
            "layers": [
                {
                    "id": "bg",
                    "type": "shape",
                    "shape": "roundedRect",
                    "x": 0,
                    "y": 0,
                    "width": 390,
                    "height": 844,
                },
                {
                    "id": "line-1",
                    "type": "shape",
                    "shape": "line",
                    "x": 20,
                    "y": 300,
                    "width": 100,
                    "height": 0,
                    "strokeWidth": 1,
                },
                {
                    "id": "dot-1",
                    "type": "shape",
                    "shape": "circle",
                    "x": 20,
                    "y": 400,
                    "width": 3,
                    "height": 3,
                },
            ],
        }
    )

    assert result["ok"] is True
    assert result["errors"] == []


def test_layout_validator_keeps_large_blob_out_of_time_safe_area_after_recheck():
    dsl = {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "background": {"type": "color", "value": "#020617"},
        "layers": [
            {
                "id": "ambient-blob",
                "type": "shape",
                "shape": "blob",
                "role": "decoration",
                "x": 80,
                "y": 120,
                "width": 240,
                "height": 180,
            }
        ],
    }

    first = validate_layout(dsl, "", {})
    second = validate_layout(first["dsl"], "", {})

    assert first["errors"][0]["type"] == "safe_area_overlap"
    assert second["errors"] == []


def test_semantic_validator_accepts_crescent_for_moon():
    result = validate_semantics(
        {
            "theme": "night",
            "background": {"value": "#020617"},
            "layers": [
                {
                    "id": "night-crescent",
                    "type": "shape",
                    "shape": "crescent",
                    "x": 42,
                    "y": 86,
                    "width": 64,
                    "height": 64,
                }
            ],
        },
        "night lockscreen with a moon",
    )

    assert not any(
        error.get("target") == "moon" for error in result["errors"]
    )


def test_semantic_validator_accepts_fallback_star_for_star():
    result = validate_semantics(
        {
            "theme": "night",
            "background": {"value": "#020617"},
            "layers": [
                {
                    "id": "fallback_star",
                    "type": "shape",
                    "shape": "star",
                    "fallback": True,
                    "x": 24,
                    "y": 300,
                    "width": 18,
                    "height": 18,
                }
            ],
        },
        "night lockscreen with stars",
    )

    assert not any(
        error.get("target") == "star" for error in result["errors"]
    )
