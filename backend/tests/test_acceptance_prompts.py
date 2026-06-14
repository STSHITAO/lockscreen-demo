from orchestrator import generate_lockscreen_with_agent_loop
from validators.layout_validator import classify_region, find_target_layers


def _base_dsl(theme: str, background: str, layers: list[dict]) -> dict:
    return {
        "version": "1.0",
        "canvas": {"width": 390, "height": 844},
        "theme": theme,
        "mode": "static",
        "background": {"type": "gradient", "value": background},
        "layers": layers,
    }


def test_night_prompt_repairs_moon_to_top_left_and_adds_weather():
    prompt = "生成一个夜晚星空锁屏，月亮放在左上角，星星围绕四周，底部显示天气卡片。"
    draft = _base_dsl(
        "night",
        "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
        [
            {
                "id": "moon",
                "type": "shape",
                "shape": "circle",
                "x": 290,
                "y": 64,
                "width": 60,
                "height": 60,
            },
            {
                "id": "star",
                "type": "shape",
                "shape": "star",
                "x": 36,
                "y": 330,
                "width": 12,
                "height": 12,
            },
        ],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: draft,
    )

    moon = find_target_layers(result, "moon")[0]
    assert classify_region(moon["x"], moon["y"]) == "top-left"
    assert any(layer.get("role") == "weather" for layer in result["layers"])
    assert result["_debug"]["loopCount"] == 1
    assert result["_debug"]["usedFallback"] is False


def test_cute_prompt_adds_trusted_heart_asset_and_weather():
    prompt = "生成一个粉色可爱风锁屏，爱心放在右上角，底部显示天气卡片。"
    draft = _base_dsl(
        "cute",
        "linear-gradient(180deg, #f9a8d4 0%, #db2777 100%)",
        [],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: draft,
    )

    heart = find_target_layers(result, "heart")[0]
    assert heart["assetId"] == "doodle-143"
    assert heart["src"] == "/materials/svg/doodle-143.svg"
    assert classify_region(heart["x"], heart["y"]) == "top-right"
    assert any(layer.get("role") == "weather" for layer in result["layers"])
    assert result["_debug"]["usedFallback"] is False


def test_tech_prompt_repairs_weather_to_bottom_and_keeps_large_time():
    prompt = "生成一个蓝色科技风锁屏，中间显示大号时间，底部显示天气卡片。"
    draft = _base_dsl(
        "tech",
        "linear-gradient(180deg, #172554 0%, #020617 100%)",
        [
            {
                "id": "time",
                "type": "text",
                "role": "time",
                "content": "18:30",
                "x": 195,
                "y": 180,
                "fontSize": 76,
            },
            {
                "id": "weather",
                "type": "widget",
                "role": "weather",
                "x": 32,
                "y": 420,
                "width": 326,
                "height": 104,
                "content": {"title": "今日天气", "main": "26°C"},
            },
        ],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: draft,
    )

    weather = next(layer for layer in result["layers"] if layer.get("role") == "weather")
    time = next(layer for layer in result["layers"] if layer.get("role") == "time")
    assert weather["y"] >= 620
    assert time["fontSize"] >= 60
    assert result["_debug"]["usedFallback"] is False


def _missing_material_context(*targets: str) -> dict:
    return {
        "materialCandidateGroups": [
            {
                "slot": "decoration",
                "requirement": {"subjects": [target], "query": target},
                "candidates": [],
            }
            for target in targets
        ]
    }


def _fallback_targets(result: dict) -> set[str]:
    return {
        layer.get("target")
        for layer in result.get("layers", [])
        if layer.get("fallback") is True
    }


def test_missing_night_materials_use_moon_and_star_fallbacks():
    prompt = (
        "\u751f\u6210\u4e00\u4e2a\u591c\u665a\u661f\u7a7a\u9501\u5c4f\uff0c"
        "\u6708\u4eae\u653e\u5728\u5de6\u4e0a\u89d2\uff0c"
        "\u661f\u661f\u56f4\u7ed5\u56db\u5468\uff0c"
        "\u5e95\u90e8\u663e\u793a\u5929\u6c14\u5361\u7247\u3002"
    )
    draft = _base_dsl(
        "night",
        "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
        [],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: {
            "dsl": draft,
            "context": _missing_material_context("moon", "star"),
        },
    )

    assert {"moon", "star"} <= _fallback_targets(result)
    assert classify_region(find_target_layers(result, "moon")[0]["x"], find_target_layers(result, "moon")[0]["y"]) == "top-left"
    assert any(layer.get("role") == "weather" for layer in result["layers"])
    assert result["_debug"]["usedFallback"] is False


def test_missing_cute_materials_use_heart_cloud_and_star_fallbacks():
    prompt = (
        "\u751f\u6210\u4e00\u4e2a\u7c89\u8272\u53ef\u7231\u98ce\u9501\u5c4f\uff0c"
        "\u53f3\u4e0a\u89d2\u6709\u7231\u5fc3\uff0c"
        "\u5468\u56f4\u6709\u4e91\u6735\u548c\u661f\u661f\u3002"
    )
    draft = _base_dsl(
        "cute",
        "linear-gradient(180deg, #f9a8d4 0%, #db2777 100%)",
        [],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: {
            "dsl": draft,
            "context": _missing_material_context("heart", "cloud", "star"),
        },
    )

    assert {"heart", "cloud", "star"} <= _fallback_targets(result)
    heart = find_target_layers(result, "heart")[0]
    assert classify_region(heart["x"], heart["y"]) == "top-right"
    assert result["_debug"]["usedFallback"] is False


def test_missing_space_materials_use_planet_and_sparkle_fallbacks():
    prompt = (
        "\u751f\u6210\u4e00\u4e2a\u592a\u7a7a\u98ce\u9501\u5c4f\uff0c"
        "\u6709\u661f\u7403\u548c\u95ea\u5149\u88c5\u9970\u3002"
    )
    draft = _base_dsl(
        "space",
        "linear-gradient(180deg, #111827 0%, #020617 100%)",
        [],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: {
            "dsl": draft,
            "context": _missing_material_context("planet", "sparkle"),
        },
    )

    assert {"planet", "sparkle"} <= _fallback_targets(result)
    assert result["_debug"]["usedFallback"] is False


def test_missing_sky_material_uses_cloud_fallback_and_weather():
    prompt = (
        "\u751f\u6210\u4e00\u4e2a\u6e05\u65b0\u5929\u7a7a\u9501\u5c4f\uff0c"
        "\u5de6\u4e0a\u89d2\u6709\u4e91\u6735\uff0c"
        "\u5e95\u90e8\u663e\u793a\u5929\u6c14\u3002"
    )
    draft = _base_dsl(
        "sky",
        "linear-gradient(180deg, #7dd3fc 0%, #e0f2fe 100%)",
        [],
    )

    result = generate_lockscreen_with_agent_loop(
        prompt,
        draft_generator=lambda value: {
            "dsl": draft,
            "context": _missing_material_context("cloud"),
        },
    )

    assert "cloud" in _fallback_targets(result)
    cloud = find_target_layers(result, "cloud")[0]
    assert classify_region(cloud["x"], cloud["y"]) == "top-left"
    assert any(layer.get("role") == "weather" for layer in result["layers"])
    assert result["_debug"]["usedFallback"] is False
