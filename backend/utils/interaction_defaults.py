import copy
import re
from typing import Any

from utils.animation_defaults import SUPPORTED_ANIMATIONS
from utils.shape_defaults import normalize_position_hint, normalize_target


TRIGGER_TYPES = {
    "tap",
    "multiTap",
    "longPressStart",
    "longPressEnd",
    "swipeLeft",
    "swipeRight",
}
ACTION_TYPES = {
    "animate",
    "stopAnimation",
    "setAnimationSpeed",
    "burst",
    "switchCard",
    "setVisibility",
    "reset",
}
PARTICLE_SHAPES = {"heart", "star", "sparkle", "circle"}
AFTER_EFFECTS = {"restore", "hide"}

CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed == parsed else default
    except (TypeError, ValueError):
        return default


def _integer(value: Any, default: int, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(_number(value, default), maximum)))


def _decimal(
    value: Any,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(minimum, min(_number(value, default), maximum))


def _tap_count(prompt: str) -> int:
    match = re.search(
        r"(?:点击|点按|tap)(?:[^，,。.;；\n]{0,12}?)(\d+|[一二两三四五六七八九十])次",
        prompt,
        re.IGNORECASE,
    )
    if match:
        raw = match.group(1)
        return _integer(CHINESE_NUMBERS.get(raw, raw), 3, 1, 10)
    if any(token in prompt for token in ("双击", "double tap", "double-tap")):
        return 2
    return 3


def _particle_shape(target: str) -> str:
    return target if target in PARTICLE_SHAPES else "circle"


def _interaction_target(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if (
        ("card" in raw and "group" in raw)
        or raw
        in {
            "cards",
            "bottom cards",
            "bottom-cards",
            "card carousel",
            "card stack",
        }
        or (
            "card" in raw
            and any(token in raw for token in ("bottom", "carousel", "stack"))
        )
        or "卡片组" in raw
        or "卡片切换" in raw
        or "底部卡片" in raw
    ):
        return "card-group"
    return normalize_target(raw) or raw[:80]


def normalize_trigger(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        value = {"type": value}
    if not isinstance(value, dict):
        return None
    trigger_type = str(value.get("type") or "").strip()
    if trigger_type not in TRIGGER_TYPES:
        return None
    trigger: dict[str, Any] = {"type": trigger_type}
    if trigger_type == "multiTap":
        trigger["count"] = _integer(value.get("count"), 3, 1, 10)
        trigger["withinMs"] = _integer(
            value.get("withinMs"),
            1200,
            300,
            3000,
        )
    elif trigger_type == "longPressStart":
        trigger["durationMs"] = _integer(
            value.get("durationMs"),
            500,
            250,
            3000,
        )
    return trigger


def normalize_action(value: Any, target: str = "") -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    action_type = str(value.get("type") or "").strip()
    if action_type not in ACTION_TYPES:
        return None

    action: dict[str, Any] = {"type": action_type}
    if action_type == "animate":
        animation = str(value.get("animation") or "").strip()
        if animation not in SUPPORTED_ANIMATIONS:
            animation = "pulse" if target == "heart" else "twinkle"
        action.update(
            {
                "animation": animation,
                "duration": _integer(value.get("duration"), 600, 80, 5000),
                "speed": _decimal(value.get("speed"), 1, 0.25, 5),
                "intensity": _decimal(
                    value.get("intensity"),
                    1,
                    0.5,
                    3,
                ),
                "repeat": _integer(value.get("repeat"), 1, 1, 10),
            }
        )
        if value.get("until") == "release":
            action["until"] = "release"
    elif action_type == "setAnimationSpeed":
        action["speed"] = _decimal(value.get("speed"), 1, 0.25, 5)
    elif action_type == "burst":
        source = (
            copy.deepcopy(value.get("particleSource"))
            if isinstance(value.get("particleSource"), dict)
            else {
                "type": "shape",
                "shape": _particle_shape(target),
            }
        )
        if source.get("type") == "shape":
            shape = str(source.get("shape") or _particle_shape(target))
            source = {
                "type": "shape",
                "shape": shape if shape in PARTICLE_SHAPES else "circle",
            }
        elif source.get("type") == "asset":
            source = {
                "type": "asset",
                "assetId": str(source.get("assetId") or ""),
            }
        else:
            source = {
                "type": "shape",
                "shape": _particle_shape(target),
            }
        after_effect = str(value.get("afterEffect") or "restore")
        action.update(
            {
                "particleSource": source,
                "count": _integer(value.get("count"), 12, 1, 40),
                "duration": _integer(
                    value.get("duration"),
                    800,
                    80,
                    5000,
                ),
                "afterEffect": (
                    after_effect
                    if after_effect in AFTER_EFFECTS
                    else "restore"
                ),
                "restoreDelay": _integer(
                    value.get("restoreDelay"),
                    0,
                    0,
                    5000,
                ),
            }
        )
    elif action_type == "switchCard":
        direction = str(value.get("direction") or "next")
        if direction == "prev":
            direction = "previous"
        action["direction"] = (
            direction if direction in {"next", "previous"} else "next"
        )
    elif action_type == "setVisibility":
        action["visible"] = bool(value.get("visible", True))
    return action


def _merge_actions(
    existing: list[dict[str, Any]],
    explicit: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = copy.deepcopy(existing)
    indexes = {
        str(action.get("type") or ""): index
        for index, action in enumerate(merged)
        if isinstance(action, dict)
    }
    for action in explicit:
        action_type = str(action.get("type") or "")
        if action_type in indexes:
            merged[indexes[action_type]] = copy.deepcopy(action)
        else:
            indexes[action_type] = len(merged)
            merged.append(copy.deepcopy(action))
    return merged


def _default_actions(
    target: str,
    prompt: str,
    *,
    until_release: bool = False,
) -> list[dict[str, Any]]:
    text = prompt.lower()
    actions: list[dict[str, Any]] = []
    animation = "pulse" if target == "heart" else "twinkle"
    if target in {"heart", "star", "sparkle"} and (
        any(token in text for token in ("跳动", "闪烁", "加速", "pulse", "twinkle"))
        or "爆炸" not in text
    ):
        animate = normalize_action(
            {
                "type": "animate",
                "animation": animation,
                "duration": 600,
                "speed": 3 if "加速" in text else 1.5,
                "intensity": 1.5,
                "until": "release" if until_release else None,
            },
            target,
        )
        if animate:
            actions.append(animate)
    if any(token in text for token in ("爆炸", "炸开", "burst")):
        after_effect = (
            "hide"
            if any(token in text for token in ("消失", "不恢复", "hide"))
            else "restore"
        )
        burst = normalize_action(
            {
                "type": "burst",
                "particleSource": {
                    "type": "shape",
                    "shape": _particle_shape(target),
                },
                "count": 12,
                "duration": 800,
                "afterEffect": after_effect,
            },
            target,
        )
        if burst:
            actions.append(burst)
    return actions or [{"type": "reset"}]


def extract_interaction_requirements(
    prompt: str,
) -> list[dict[str, Any]]:
    text = str(prompt or "").strip()
    lowered = text.lower()
    requirements: list[dict[str, Any]] = []

    if any(token in lowered for token in ("滑动", "swipe")):
        directions = []
        if any(token in lowered for token in ("左滑", "向左滑", "swipe left")):
            directions.append(("swipeLeft", "next"))
        if any(token in lowered for token in ("右滑", "向右滑", "swipe right")):
            directions.append(("swipeRight", "previous"))
        if not directions or any(
            token in lowered for token in ("左右滑动", "左右切换")
        ):
            directions = [
                ("swipeLeft", "next"),
                ("swipeRight", "previous"),
            ]
        for trigger_type, direction in directions:
            requirements.append(
                {
                    "target": "card-group",
                    "trigger": {"type": trigger_type},
                    "actions": [
                        {"type": "switchCard", "direction": direction}
                    ],
                    "complexity": "simple",
                }
            )

    target = normalize_target(lowered)
    if not target:
        return requirements

    if any(token in lowered for token in ("长按", "long press", "hold")):
        release_effects = [
            action
            for action in _default_actions(target, text)
            if action.get("type") == "burst"
        ]
        requirements.append(
            {
                "target": target,
                "preferredPosition": normalize_position_hint(lowered),
                "trigger": {
                    "type": "longPressStart",
                    "durationMs": 500,
                },
                "actions": _default_actions(
                    target,
                    text,
                    until_release=True,
                ),
                "releaseActions": [
                    {"type": "stopAnimation"},
                    *(release_effects or [{"type": "reset"}]),
                ],
                "complexity": "simple",
            }
        )
        return requirements

    if any(
        token in lowered
        for token in ("连续点击", "多次点击", "点击几次", "双击", "multi tap")
    ) or re.search(r"(?:点击|点按|tap).{0,12}(?:\d+|[一二两三四五六七八九十])次", lowered):
        count = _tap_count(lowered)
        requirements.append(
            {
                "target": target,
                "preferredPosition": normalize_position_hint(lowered),
                "trigger": {
                    "type": "multiTap",
                    "count": count,
                    "withinMs": max(1200, min(3000, count * 300)),
                },
                "actions": _default_actions(target, text),
                "complexity": "simple",
            }
        )
    elif any(token in lowered for token in ("点击", "点按", "tap")):
        requirements.append(
            {
                "target": target,
                "preferredPosition": normalize_position_hint(lowered),
                "trigger": {"type": "tap"},
                "actions": _default_actions(target, text),
                "complexity": "simple",
            }
        )
    return requirements


def normalize_interaction_requirements(
    value: Any,
    prompt: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        return extract_interaction_requirements(prompt)

    requirements = []
    for raw in value[:8]:
        if not isinstance(raw, dict):
            continue
        raw_target = str(raw.get("target") or "").strip().lower()
        target = _interaction_target(raw_target)
        trigger = normalize_trigger(raw.get("trigger"))
        if not target or not trigger:
            continue
        actions = [
            action
            for action in (
                normalize_action(item, target)
                for item in raw.get("actions", [])
            )
            if action
        ]
        release_actions = [
            action
            for action in (
                normalize_action(item, target)
                for item in raw.get("releaseActions", [])
            )
            if action
        ]
        raw_actions = raw.get("actions", [])
        controlled = (
            trigger is not None
            and isinstance(raw_actions, list)
            and all(
                isinstance(item, dict)
                and str(item.get("type") or "") in ACTION_TYPES
                for item in raw_actions
            )
        )
        requirements.append(
            {
                "target": target,
                "targetId": str(raw.get("targetId") or ""),
                "preferredPosition": normalize_position_hint(
                    raw.get("preferredPosition")
                ),
                "trigger": trigger,
                "actions": actions or [{"type": "reset"}],
                "releaseActions": release_actions,
                "complexity": "simple" if controlled else "complex",
            }
        )
    prompt_requirements = extract_interaction_requirements(prompt)
    by_key = {
        (
            requirement["target"],
            requirement["trigger"]["type"],
        ): index
        for index, requirement in enumerate(requirements)
    }
    for prompt_requirement in prompt_requirements:
        key = (
            prompt_requirement["target"],
            prompt_requirement["trigger"]["type"],
        )
        if key in by_key:
            existing = requirements[by_key[key]]
            requirements[by_key[key]] = {
                **existing,
                **prompt_requirement,
                "actions": _merge_actions(
                    existing.get("actions", []),
                    prompt_requirement.get("actions", []),
                ),
                "releaseActions": _merge_actions(
                    existing.get("releaseActions", []),
                    prompt_requirement.get("releaseActions", []),
                ),
                "targetId": existing.get("targetId", ""),
                "preferredPosition": (
                    existing.get("preferredPosition")
                    or prompt_requirement.get("preferredPosition")
                    or "center"
                ),
            }
        elif len(requirements) < 8:
            by_key[key] = len(requirements)
            requirements.append(prompt_requirement)
    return requirements or prompt_requirements
