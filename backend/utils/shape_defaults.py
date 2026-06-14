import re
from typing import Any


TARGET_SHAPES = {
    "moon": "crescent",
    "star": "star",
    "heart": "heart",
    "cloud": "cloud",
    "sparkle": "sparkle",
    "planet": "planet",
    "circle": "circle",
    "blob": "blob",
}

TARGET_ALIASES = {
    "moon": ("moon", "\u6708\u4eae", "\u6708\u7403"),
    "star": ("star", "stars", "\u661f\u661f", "\u661f\u7a7a"),
    "heart": ("heart", "\u7231\u5fc3", "\u5fc3\u5f62"),
    "cloud": ("cloud", "clouds", "\u4e91\u6735", "\u4e91"),
    "sparkle": (
        "sparkle",
        "sparkles",
        "glint",
        "\u95ea\u5149",
        "\u95ea\u70c1",
    ),
    "planet": ("planet", "\u661f\u7403", "\u884c\u661f"),
    "circle": ("circle", "dot", "dots", "\u5706", "\u5706\u70b9"),
    "blob": ("blob", "glow blob", "\u5149\u6591", "\u6a21\u7cca\u5149\u6591"),
}

POSITION_ALIASES = {
    "top-left": (
        "top-left",
        "top left",
        "\u5de6\u4e0a\u89d2",
        "\u5de6\u4e0a",
    ),
    "top-right": (
        "top-right",
        "top right",
        "\u53f3\u4e0a\u89d2",
        "\u53f3\u4e0a",
    ),
    "bottom-left": (
        "bottom-left",
        "bottom left",
        "\u5de6\u4e0b\u89d2",
        "\u5de6\u4e0b",
    ),
    "bottom-right": (
        "bottom-right",
        "bottom right",
        "\u53f3\u4e0b\u89d2",
        "\u53f3\u4e0b",
    ),
    "around": (
        "around",
        "surrounding",
        "\u5468\u56f4",
        "\u56db\u5468",
        "\u73af\u7ed5",
    ),
    "bottom": ("bottom", "\u5e95\u90e8", "\u4e0b\u65b9"),
    "center": (
        "center",
        "middle",
        "\u4e2d\u95f4",
        "\u4e2d\u592e",
    ),
}

SHAPE_DEFAULTS = {
    "moon": {"width": 64, "height": 64, "animation": "float"},
    "star": {"width": 22, "height": 22, "animation": "pulse"},
    "heart": {"width": 52, "height": 48, "animation": "pulse"},
    "cloud": {"width": 88, "height": 52, "animation": "float"},
    "sparkle": {"width": 30, "height": 30, "animation": "pulse"},
    "planet": {"width": 78, "height": 78, "animation": "rotate"},
    "circle": {"width": 20, "height": 20, "animation": "pulse"},
    "blob": {"width": 112, "height": 96, "animation": "float"},
}

THEME_COLORS = {
    "night": {
        "moon": "#f8fafc",
        "star": "#fef3c7",
        "heart": "#f9a8d4",
        "cloud": "#cbd5e1",
        "sparkle": "#e0f2fe",
        "planet": "#a5b4fc",
        "circle": "#e2e8f0",
        "blob": "rgba(96,165,250,0.42)",
    },
    "cute": {
        "moon": "#fff7ed",
        "star": "#fef08a",
        "heart": "#fb7185",
        "cloud": "#fff1f2",
        "sparkle": "#fdf2f8",
        "planet": "#c4b5fd",
        "circle": "#fbcfe8",
        "blob": "rgba(244,114,182,0.38)",
    },
    "space": {
        "moon": "#e2e8f0",
        "star": "#ffffff",
        "heart": "#f0abfc",
        "cloud": "#94a3b8",
        "sparkle": "#67e8f9",
        "planet": "#818cf8",
        "circle": "#c4b5fd",
        "blob": "rgba(129,140,248,0.4)",
    },
}


def normalize_target(target: Any) -> str | None:
    text = str(target or "").strip().lower().replace("_", "-")
    if not text:
        return None
    if text in TARGET_SHAPES:
        return text
    for canonical, aliases in TARGET_ALIASES.items():
        if any(alias.lower() == text for alias in aliases):
            return canonical
    for canonical, aliases in TARGET_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            return canonical
    return None


def normalize_position_hint(position_hint: Any) -> str:
    text = str(position_hint or "").strip().lower().replace("_", "-")
    for canonical, aliases in POSITION_ALIASES.items():
        if text == canonical or any(alias.lower() in text for alias in aliases):
            return canonical
    return "center"


def infer_position_hint(prompt: str, target: str) -> str | None:
    text = str(prompt or "").lower()
    canonical = normalize_target(target)
    if not canonical:
        return None
    aliases = TARGET_ALIASES[canonical]
    clauses = [
        clause.strip()
        for clause in re.split(r"[,.;:!?\n\u3002\uff0c\uff1b\uff1a\uff01\uff1f]+", text)
        if clause.strip()
    ]
    for clause in clauses:
        if not any(alias.lower() in clause for alias in aliases):
            continue
        for position, position_aliases in POSITION_ALIASES.items():
            if any(alias.lower() in clause for alias in position_aliases):
                return position
    return None


def shape_satisfies_target(layer: dict[str, Any], target: str) -> bool:
    canonical = normalize_target(target)
    if not canonical or not isinstance(layer, dict):
        return False
    shape = str(layer.get("shape") or "").lower()
    layer_id = str(layer.get("id") or "").lower()
    layer_target = normalize_target(layer.get("target"))
    if shape == TARGET_SHAPES[canonical]:
        return True
    if layer_target == canonical:
        return True
    return bool(layer.get("fallback")) and f"fallback_{canonical}" in layer_id


def target_aliases(target: str) -> tuple[str, ...]:
    canonical = normalize_target(target)
    return TARGET_ALIASES.get(canonical or "", (str(target or "").lower(),))
