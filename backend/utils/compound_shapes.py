import copy
import re
from typing import Any


COMPOUND_PRIMITIVES = {
    "circle",
    "ellipse",
    "rect",
    "roundedRect",
    "triangle",
    "polygon",
    "line",
}
MAX_COMPOUND_PARTS = 24


def _number(value: Any, fallback: float = 0) -> float:
    try:
        parsed = float(value)
        return parsed if parsed == parsed else fallback
    except (TypeError, ValueError):
        return fallback


def _clamp(value: Any, minimum: float = 0, maximum: float = 1) -> float:
    return round(max(minimum, min(_number(value), maximum)), 4)


def _color(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 80:
        return fallback
    return text


def _points(value: Any, maximum: int = 12) -> list[list[float]]:
    if not isinstance(value, list):
        return []
    points = []
    for raw in value[:maximum]:
        if not isinstance(raw, (list, tuple)) or len(raw) < 2:
            continue
        points.append([_clamp(raw[0]), _clamp(raw[1])])
    return points


def normalize_compound_parts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    parts: list[dict[str, Any]] = []
    for raw in value[:MAX_COMPOUND_PARTS]:
        if not isinstance(raw, dict):
            continue
        shape = str(raw.get("shape") or "").strip()
        if shape not in COMPOUND_PRIMITIVES:
            continue
        part: dict[str, Any] = {
            "shape": shape,
            "fill": _color(raw.get("fill"), "transparent"),
            "stroke": _color(raw.get("stroke"), "transparent"),
            "strokeWidth": _clamp(raw.get("strokeWidth"), 0, 0.2),
            "opacity": _clamp(raw.get("opacity", 1)),
            "rotation": round(_number(raw.get("rotation")), 2),
        }
        if shape in {"triangle", "polygon"}:
            points = _points(raw.get("points"), 3 if shape == "triangle" else 12)
            if len(points) < 3:
                continue
            part["points"] = points
        else:
            part.update(
                {
                    "x": _clamp(raw.get("x")),
                    "y": _clamp(raw.get("y")),
                    "width": _clamp(raw.get("width")),
                    "height": _clamp(raw.get("height")),
                }
            )
            if shape == "circle":
                size = min(part["width"], part["height"])
                part["width"] = size
                part["height"] = size
            if shape == "roundedRect":
                part["radius"] = _clamp(raw.get("radius", 0.12), 0, 0.5)
        parts.append(part)
    return parts


def safe_compound_id(target: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(target or "").lower()).strip("-")
    return slug[:48] or "object"


def copy_compound_parts(value: Any) -> list[dict[str, Any]]:
    return copy.deepcopy(normalize_compound_parts(value))
