import copy
import re
from typing import Any

from material_catalog import get_asset
from utils.shape_defaults import (
    TARGET_ALIASES as FALLBACK_TARGET_ALIASES,
    shape_satisfies_target,
)


POSITION_ALIASES = {
    "top-left": ("左上角", "左上", "top-left", "top left"),
    "top-right": ("右上角", "右上", "top-right", "top right"),
    "bottom-left": ("左下角", "左下", "bottom-left", "bottom left"),
    "bottom-right": ("右下角", "右下", "bottom-right", "bottom right"),
    "bottom": ("底部", "下方", "bottom"),
    "center": ("中间", "中央", "center", "middle"),
}
TARGET_ALIASES = {
    "moon": ("moon", "月亮", "月球"),
    "star": ("star", "stars", "星星", "星空"),
    "heart": ("heart", "爱心", "心形"),
    "weather": ("weather", "天气"),
}
for _target, _aliases in FALLBACK_TARGET_ALIASES.items():
    TARGET_ALIASES[_target] = _aliases


def _number(value: Any, fallback: float = 0) -> float:
    try:
        parsed = float(value)
        return parsed if parsed == parsed else fallback
    except (TypeError, ValueError):
        return fallback


def classify_region(x: Any, y: Any) -> str:
    x_value = _number(x)
    y_value = _number(y)
    if x_value < 130 and y_value < 220:
        return "top-left"
    if x_value > 240 and y_value < 220:
        return "top-right"
    if x_value < 130 and y_value > 620:
        return "bottom-left"
    if x_value > 240 and y_value > 620:
        return "bottom-right"
    if 110 <= x_value <= 280 and 260 <= y_value <= 620:
        return "center"
    if y_value > 620:
        return "bottom"
    return "other"


def region_matches(
    actual: str,
    expected: str,
    layer: dict[str, Any] | None = None,
) -> bool:
    if (
        expected in {"bottom", "bottom-left", "bottom-right"}
        and isinstance(layer, dict)
        and layer.get("fallback")
    ):
        x = _number(layer.get("x"))
        y = _number(layer.get("y"))
        height = _number(layer.get("height"), 40)
        in_safe_bottom_band = y >= 520 and y + height <= 660
        if expected == "bottom" and in_safe_bottom_band:
            return True
        if expected == "bottom-left" and in_safe_bottom_band and x < 130:
            return True
        if expected == "bottom-right" and in_safe_bottom_band and x > 240:
            return True
    if expected == "bottom":
        return actual in {"bottom", "bottom-left", "bottom-right"}
    return actual == expected


def extract_position_requirements(prompt: str) -> dict[str, str]:
    text = str(prompt or "").lower()
    requirements: dict[str, str] = {}
    clauses = [clause.strip() for clause in re.split(r"[，,。.;；\n]+", text) if clause.strip()]
    for clause in clauses:
        regions = [
            region
            for region, aliases in POSITION_ALIASES.items()
            if any(alias in clause for alias in aliases)
        ]
        if not regions:
            continue
        for target, aliases in TARGET_ALIASES.items():
            if any(alias in clause for alias in aliases):
                requirements[target] = regions[0]
    return requirements


def layer_matches_target(layer: dict[str, Any], target: str) -> bool:
    if shape_satisfies_target(layer, target):
        return True
    aliases = TARGET_ALIASES.get(target, (target,))
    values = [
        layer.get("id"),
        layer.get("role"),
        layer.get("shape"),
        layer.get("target"),
    ]
    material = get_asset(str(layer.get("assetId") or ""))
    if material:
        values.extend(material.get("subjects") or [])
        values.extend(material.get("keywords") or [])
        values.extend((material.get("name") or {}).values())
    haystack = " ".join(str(value or "").lower() for value in values)
    return any(alias.lower() in haystack for alias in aliases)


def find_target_layers(dsl: dict[str, Any], target: str) -> list[dict[str, Any]]:
    return [
        layer
        for layer in dsl.get("layers", [])
        if isinstance(layer, dict) and layer_matches_target(layer, target)
    ]


def _position_for(region: str, width: float, height: float) -> tuple[float, float]:
    positions = {
        "top-left": (24, 64),
        "top-right": (390 - width - 24, 64),
        "bottom-left": (24, 844 - height - 24),
        "bottom-right": (390 - width - 24, 844 - height - 24),
        "bottom": ((390 - width) / 2, 844 - height - 34),
        "center": ((390 - width) / 2, (844 - height) / 2),
    }
    return positions.get(region, (24, 64))


def _intersects(
    x: float,
    y: float,
    width: float,
    height: float,
    rect: tuple[float, float, float, float],
) -> bool:
    left, top, right, bottom = rect
    return x < right and x + width > left and y < bottom and y + height > top


def _is_background_layer(
    layer: dict[str, Any],
    canvas_width: float,
    canvas_height: float,
) -> bool:
    identity = " ".join(
        (
            str(layer.get("id") or ""),
            str(layer.get("role") or ""),
            str(layer.get("target") or ""),
        )
    ).lower()
    width = _number(layer.get("width"))
    height = _number(layer.get("height"))
    named_background = any(
        name in identity for name in ("background", "bg", "backdrop")
    )
    large_sky = (
        "sky" in identity
        and width >= canvas_width * 0.8
        and height >= canvas_height * 0.5
    )
    return (
        named_background
        or large_sky
        or (width >= canvas_width * 0.95 and height >= canvas_height * 0.95)
    )


def validate_layout(
    dsl: Any,
    prompt: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixed = copy.deepcopy(dsl) if isinstance(dsl, dict) else {"layers": []}
    canvas = fixed.get("canvas") if isinstance(fixed.get("canvas"), dict) else {}
    canvas_width = _number(canvas.get("width"), 390)
    canvas_height = _number(canvas.get("height"), 844)
    errors: list[dict[str, Any]] = []
    position_requirements = extract_position_requirements(prompt)

    for layer in fixed.get("layers", []):
        if not isinstance(layer, dict) or layer.get("type") == "text":
            continue
        layer_id = str(layer.get("id") or "layer")
        width = _number(layer.get("width"), 40)
        height = _number(layer.get("height"), width)
        is_line = layer.get("type") == "shape" and layer.get("shape") == "line"
        min_size = (
            24
            if layer.get("type")
            in {
                "asset",
                "frameAnimation",
                "widget",
                "glassCard",
                "compoundShape",
            }
            else 2
        )
        resized = False
        if width < min_size or width > canvas_width:
            width = max(min_size, min(width, canvas_width))
            resized = True
        minimum_height = 0 if is_line else min_size
        if height < minimum_height or height > canvas_height:
            height = max(minimum_height, min(height, canvas_height))
            resized = True
        if resized:
            errors.append(
                {
                    "type": "layout_size_invalid",
                    "level": "error",
                    "layerId": layer_id,
                    "message": "layer 尺寸不合理，已限制到画布范围",
                }
            )
        layer["width"] = width
        layer["height"] = height

        x = _number(layer.get("x"))
        y = _number(layer.get("y"))
        clamped_x = max(0, min(x, canvas_width - width))
        clamped_y = max(0, min(y, canvas_height - height))
        if clamped_x != x or clamped_y != y:
            errors.append(
                {
                    "type": "layout_out_of_bounds",
                    "level": "error",
                    "layerId": layer_id,
                    "message": "layer 严重超出画布，已移回可视区域",
                }
            )
            x, y = clamped_x, clamped_y
        layer["x"], layer["y"] = x, y

    for target, expected in position_requirements.items():
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
                        "message": f"用户要求 {target} 在 {expected}，当前位于 {actual}",
                    }
                )
                width = _number(layer.get("width"), 60)
                height = _number(layer.get("height"), width)
                layer["x"], layer["y"] = _position_for(expected, width, height)

    expected_layer_ids = {
        str(layer.get("id"))
        for target in position_requirements
        for layer in find_target_layers(fixed, target)
    }
    for layer in fixed.get("layers", []):
        if (
            not isinstance(layer, dict)
            or layer.get("type")
            not in {"asset", "frameAnimation", "shape", "compoundShape"}
            or str(layer.get("id")) in expected_layer_ids
            or _is_background_layer(layer, canvas_width, canvas_height)
        ):
            continue
        x = _number(layer.get("x"))
        y = _number(layer.get("y"))
        width = _number(layer.get("width"), 40)
        height = _number(layer.get("height"), width)
        if _intersects(x, y, width, height, (90, 100, 300, 260)):
            errors.append(
                {
                    "type": "safe_area_overlap",
                    "level": "error",
                    "layerId": str(layer.get("id") or ""),
                    "target": "time",
                    "message": "装饰元素遮挡时间安全区，已移到边缘",
                }
            )
            if width > 78:
                layer["x"] = max(0, min((canvas_width - width) / 2, canvas_width - width))
                layer["y"] = 280
            elif x < canvas_width / 2:
                layer["x"] = max(0, 90 - width - 12)
                layer["y"] = 64
            else:
                layer["x"] = min(canvas_width - width, 300 + 12)
                layer["y"] = 64
        if _intersects(x, y, width, height, (24, 660, 366, 810)):
            errors.append(
                {
                    "type": "safe_area_overlap",
                    "level": "error",
                    "layerId": str(layer.get("id") or ""),
                    "target": "weather",
                    "message": "装饰元素遮挡天气卡片安全区，已上移",
                }
            )
            layer["y"] = max(270, 620 - height - 12)

    for layer in fixed.get("layers", []):
        if isinstance(layer, dict) and layer.get("role") == "weather":
            y = _number(layer.get("y"))
            if y < 620:
                errors.append(
                    {
                        "type": "position_mismatch",
                        "level": "error",
                        "target": "weather",
                        "layerId": str(layer.get("id") or ""),
                        "expected": "bottom",
                        "actual": classify_region(layer.get("x"), y),
                        "message": "天气卡片应位于底部，已移动到底部安全区",
                    }
                )
                layer["y"] = 690

    return {"ok": not errors, "errors": errors, "dsl": fixed}
