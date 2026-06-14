import copy
from typing import Any

from agents.fallback_draw_agent import create_fallback_layer
from utils.interaction_defaults import normalize_interaction_requirements
from utils.shape_defaults import normalize_target
from validators.layout_validator import find_target_layers


def _notice(target: str, message: str) -> dict[str, str]:
    return {
        "type": "interaction_unavailable",
        "level": "warning",
        "target": target,
        "message": message,
    }


def _interaction_id(target_id: str, trigger_type: str) -> str:
    return f"{target_id}-{trigger_type}".replace("_", "-").lower()


def _card_layers(dsl: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        layer
        for layer in dsl.get("layers", [])
        if isinstance(layer, dict)
        and layer.get("type") in {"widget", "glassCard"}
    ]


def apply_interaction_requirements(
    dsl: dict[str, Any],
    prompt: str,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    current = copy.deepcopy(dsl)
    current.setdefault("layers", [])
    current.setdefault("cardGroups", [])
    current.setdefault("interactions", [])
    interaction_context = context or {}
    intent = (
        interaction_context.get("intent")
        if isinstance(interaction_context.get("intent"), dict)
        else {}
    )
    requirements = normalize_interaction_requirements(
        intent.get("interactionRequirements"),
        prompt,
    )
    applied = []
    notices = []
    existing_by_key = {}
    for interaction in current["interactions"]:
        if not isinstance(interaction, dict):
            continue
        trigger_value = interaction.get("trigger")
        trigger_type = (
            str(trigger_value.get("type") or "")
            if isinstance(trigger_value, dict)
            else str(trigger_value or "")
        )
        existing_by_key[
            (str(interaction.get("targetId") or ""), trigger_type)
        ] = interaction

    for requirement in requirements:
        target = requirement["target"]
        if requirement.get("complexity") == "complex":
            notices.append(
                _notice(
                    target,
                    f"“{target}”交互较复杂，暂时无法自主生成。",
                )
            )
            continue

        trigger = requirement["trigger"]
        trigger_type = trigger["type"]
        if target == "card-group":
            cards = _card_layers(current)
            if not cards:
                notices.append(
                    _notice("card-group", "没有可切换的卡片图层。")
                )
                continue
            card_ids = {str(card["id"]) for card in cards}
            group = next(
                (
                    item
                    for item in current["cardGroups"]
                    if isinstance(item, dict)
                    and item.get("id")
                    and any(
                        str(card_id) in card_ids
                        for card_id in item.get("cardIds", [])
                    )
                ),
                None,
            )
            if group is None:
                group = {
                    "id": "info-cards",
                    "cardIds": [str(card["id"]) for card in cards],
                    "activeIndex": 0,
                    "loop": True,
                    "transition": "slide",
                }
                current["cardGroups"].append(group)
            target_id = str(group["id"])
        else:
            canonical = normalize_target(target)
            target_id = str(requirement.get("targetId") or "")
            layer = next(
                (
                    item
                    for item in current["layers"]
                    if isinstance(item, dict)
                    and str(item.get("id") or "") == target_id
                ),
                None,
            )
            if layer is None and canonical:
                matches = find_target_layers(current, canonical)
                layer = matches[0] if matches else None
            if layer is None and canonical:
                layer = create_fallback_layer(
                    canonical,
                    requirement.get("preferredPosition"),
                    str(current.get("theme") or ""),
                    current.get("canvas") or {"width": 390, "height": 844},
                )
                layer["fallbackReason"] = "interaction_target_missing"
                current["layers"].append(layer)
            if layer is None:
                notices.append(
                    _notice(target, f"没有可绑定“{target}”交互的视觉元素。")
                )
                continue
            target_id = str(layer["id"])

        key = (target_id, trigger_type)
        existing_interaction = existing_by_key.get(key)
        if existing_interaction is not None:
            existing_interaction["trigger"] = copy.deepcopy(trigger)
            existing_interaction["actions"] = copy.deepcopy(
                requirement["actions"]
            )
            existing_interaction["restart"] = "restart"
            applied.append(
                {
                    "target": target,
                    "targetId": target_id,
                    "trigger": trigger_type,
                }
            )
        else:
            interaction = {
                "id": _interaction_id(target_id, trigger_type),
                "targetId": target_id,
                "trigger": copy.deepcopy(trigger),
                "actions": copy.deepcopy(requirement["actions"]),
                "restart": "restart",
            }
            current["interactions"].append(interaction)
            existing_by_key[key] = interaction
            applied.append(
                {
                    "target": target,
                    "targetId": target_id,
                    "trigger": trigger_type,
                }
            )

        release_actions = requirement.get("releaseActions") or []
        release_key = (target_id, "longPressEnd")
        if release_actions:
            existing_release = existing_by_key.get(release_key)
            if existing_release is not None:
                existing_release["trigger"] = {"type": "longPressEnd"}
                existing_release["actions"] = copy.deepcopy(release_actions)
                existing_release["restart"] = "restart"
            else:
                release_interaction = {
                    "id": _interaction_id(target_id, "longPressEnd"),
                    "targetId": target_id,
                    "trigger": {"type": "longPressEnd"},
                    "actions": copy.deepcopy(release_actions),
                    "restart": "restart",
                }
                current["interactions"].append(release_interaction)
                existing_by_key[release_key] = release_interaction
            applied.append(
                {
                    "target": target,
                    "targetId": target_id,
                    "trigger": "longPressEnd",
                }
            )

    if applied:
        current["mode"] = "dynamic"
    existing_notices = (
        current.get("interactionNotices")
        if isinstance(current.get("interactionNotices"), list)
        else []
    )
    current["interactionNotices"] = copy.deepcopy(existing_notices)
    for notice in notices:
        if notice not in current["interactionNotices"]:
            current["interactionNotices"].append(copy.deepcopy(notice))
    return {
        "dsl": current,
        "applied": applied,
        "notices": notices,
        "requirements": requirements,
    }
