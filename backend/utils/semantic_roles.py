import re
from typing import Any


ROLE_ALIASES = {
    "clock": "time",
    "time-display": "time",
    "\u65f6\u95f4": "time",
    "day": "date",
    "date-label": "date",
    "\u65e5\u671f": "date",
    "forecast": "weather",
    "weather-card": "weather",
    "\u5929\u6c14": "weather",
    "agenda": "schedule",
    "calendar": "schedule",
    "\u65e5\u7a0b": "schedule",
    "audio": "music",
    "now-playing": "music",
    "music-player": "music",
    "\u97f3\u4e50": "music",
}
ROLE_KEYWORDS = {
    "time": ("time", "clock", "\u65f6\u95f4"),
    "date": ("date", "day", "\u65e5\u671f"),
    "weather": ("weather", "forecast", "\u5929\u6c14"),
    "schedule": ("schedule", "agenda", "calendar", "\u65e5\u7a0b"),
    "music": ("music", "audio", "now playing", "\u97f3\u4e50"),
}


def _content_text(content: Any) -> str:
    if isinstance(content, dict):
        return " ".join(str(value or "") for value in content.values())
    return str(content or "")


def _contains_keyword(text: str, keyword: str) -> bool:
    if any(ord(char) > 127 for char in keyword):
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def infer_semantic_role(layer: dict[str, Any]) -> str:
    role = str(layer.get("role") or "").strip().lower()
    if role in ROLE_ALIASES:
        return ROLE_ALIASES[role]
    if role in ROLE_KEYWORDS:
        return role
    identity = " ".join((str(layer.get("id") or ""), role)).lower()
    content = _content_text(layer.get("content")).lower()
    for haystack in (identity, content):
        for semantic_role, keywords in ROLE_KEYWORDS.items():
            if any(_contains_keyword(haystack, keyword) for keyword in keywords):
                return semantic_role
    return role


def excluded_semantic_roles(prompt: str) -> set[str]:
    text = str(prompt or "").lower()
    excluded: set[str] = set()
    english_prefixes = (
        "no",
        "without",
        "do not add",
        "don't add",
        "do not show",
        "don't show",
        "exclude",
    )
    chinese_prefixes = (
        "\u4e0d\u8981",
        "\u4e0d\u9700\u8981",
        "\u65e0\u9700",
        "\u4e0d\u663e\u793a",
        "\u522b\u52a0",
        "\u4e0d\u8981\u52a0\u5165",
    )
    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            escaped = re.escape(keyword)
            if any(
                re.search(rf"\b{re.escape(prefix)}\b.{{0,24}}\b{escaped}\b", text)
                for prefix in english_prefixes
            ) or any(
                re.search(rf"{re.escape(prefix)}.{{0,8}}{escaped}", text)
                for prefix in chinese_prefixes
            ):
                excluded.add(role)
                break
    return excluded
