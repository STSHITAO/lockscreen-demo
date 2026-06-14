import copy
from typing import Any

from .layout_validator import (
    classify_region,
    extract_position_requirements,
    find_target_layers,
    region_matches,
)
from utils.shape_defaults import TARGET_ALIASES


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _semantic_error(target: str, message: str) -> dict[str, str]:
    return {
        "type": "semantic_missing",
        "level": "error",
        "target": target,
        "message": message,
    }


def validate_semantics(
    dsl: Any,
    prompt: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixed = copy.deepcopy(dsl) if isinstance(dsl, dict) else {"layers": []}
    errors: list[dict[str, Any]] = []
    text = str(prompt or "").lower()
    theme_text = " ".join(
        (
            str(fixed.get("theme") or ""),
            str((fixed.get("background") or {}).get("value") or ""),
        )
    ).lower()

    theme_rules = (
        (
            "night",
            ("night", "夜晚", "星空", "深色", "dark"),
            ("night", "dark", "space", "#020617", "#0f172a", "#000", "#111"),
        ),
        (
            "cute",
            ("cute", "可爱", "粉色", "pink"),
            ("cute", "pink", "rose", "#ec4899", "#f9a8d4", "#f472b6"),
        ),
        (
            "tech",
            ("tech", "科技", "蓝色", "blue"),
            ("tech", "blue", "cyan", "#0f172a", "#172554", "#1e3a8a", "#0284c7"),
        ),
    )
    for target, prompt_keywords, result_keywords in theme_rules:
        if _contains_any(text, prompt_keywords) and not _contains_any(
            theme_text, result_keywords
        ):
            errors.append(
                _semantic_error(target, f"用户要求 {target} 风格，但主题或背景不匹配")
            )

    layers = fixed.get("layers") if isinstance(fixed.get("layers"), list) else []
    if _contains_any(text, ("weather", "天气")) and not any(
        isinstance(layer, dict) and layer.get("role") == "weather"
        for layer in layers
    ):
        errors.append(_semantic_error("weather", "用户要求天气卡片，但 DSL 中没有 weather layer"))

    target_rules = TARGET_ALIASES
    unavailable = {
        str(value).strip().lower()
        for value in (context or {}).get("unavailableVisuals", [])
    }
    for target, keywords in target_rules.items():
        if target in unavailable:
            continue
        if _contains_any(text, keywords) and not find_target_layers(fixed, target):
            errors.append(
                _semantic_error(target, f"用户要求 {target}，但 DSL 中没有对应元素")
            )

    for target, expected in extract_position_requirements(prompt).items():
        for layer in find_target_layers(fixed, target):
            actual = classify_region(layer.get("x"), layer.get("y"))
            if not region_matches(actual, expected, layer):
                errors.append(
                    {
                        "type": "position_mismatch",
                        "level": "error",
                        "target": target,
                        "layerId": str(layer.get("id") or ""),
                        "expected": expected,
                        "actual": actual,
                        "message": f"{target} 的位置不满足用户要求",
                    }
                )

    return {"ok": not errors, "errors": errors, "dsl": fixed}
