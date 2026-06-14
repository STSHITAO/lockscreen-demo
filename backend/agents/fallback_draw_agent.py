from typing import Any

from utils.shape_defaults import (
    SHAPE_DEFAULTS,
    TARGET_SHAPES,
    THEME_COLORS,
    normalize_position_hint,
    normalize_target,
)


def _number(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _position(
    hint: str,
    canvas_width: float,
    canvas_height: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    margin_x = max(24, canvas_width * 0.08)
    top = max(64, canvas_height * 0.1)
    bottom_y = min(
        canvas_height - height - 24,
        canvas_height * 0.78 - height - 12,
    )
    positions = {
        "top-left": (margin_x, top),
        "top-right": (canvas_width - width - margin_x, top),
        "bottom-left": (margin_x, bottom_y),
        "bottom-right": (canvas_width - width - margin_x, bottom_y),
        "bottom": ((canvas_width - width) / 2, bottom_y),
        "center": (
            (canvas_width - width) / 2,
            (canvas_height - height) / 2,
        ),
        "around": (margin_x, canvas_height * 0.38),
    }
    x, y = positions.get(hint, positions["center"])
    return max(0, round(x, 2)), max(0, round(y, 2))


def create_fallback_layer(
    target: str,
    position_hint: str | None,
    theme: str | None,
    canvas: dict,
) -> dict:
    canonical = normalize_target(target)
    if canonical is None:
        raise ValueError(f"Unsupported fallback target: {target}")

    defaults = SHAPE_DEFAULTS[canonical]
    width = defaults["width"]
    height = defaults["height"]
    canvas_width = _number((canvas or {}).get("width"), 390)
    canvas_height = _number((canvas or {}).get("height"), 844)
    hint = normalize_position_hint(position_hint)
    x, y = _position(
        hint,
        canvas_width,
        canvas_height,
        width,
        height,
    )
    theme_name = str(theme or "night").strip().lower()
    palette = THEME_COLORS.get(theme_name, THEME_COLORS["night"])

    return {
        "id": f"fallback_{canonical}",
        "type": "shape",
        "shape": TARGET_SHAPES[canonical],
        "role": "decoration",
        "target": canonical,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "color": palette[canonical],
        "opacity": 0.92,
        "animation": defaults["animation"],
        "fallback": True,
        "fallbackReason": "asset_missing",
    }
