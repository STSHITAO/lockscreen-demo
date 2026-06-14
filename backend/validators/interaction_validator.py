import copy
from typing import Any

from material_catalog import get_asset
from utils.interaction_defaults import (
    PARTICLE_SHAPES,
    normalize_action,
    normalize_trigger,
)


def _error(
    error_type: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "type": error_type,
        "level": "warning",
        "message": message,
        **details,
    }


def _notice(target: str, message: str) -> dict[str, str]:
    return {
        "type": "interaction_unavailable",
        "level": "warning",
        "target": target,
        "message": message,
    }


def validate_interactions(
    dsl: Any,
    prompt: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixed = copy.deepcopy(dsl) if isinstance(dsl, dict) else {}
    errors: list[dict[str, Any]] = []
    notices: list[dict[str, str]] = []
    layers = [
        layer
        for layer in fixed.get("layers", [])
        if isinstance(layer, dict) and layer.get("id")
    ]
    layer_ids = {str(layer["id"]) for layer in layers}
    layer_by_id = {str(layer["id"]): layer for layer in layers}

    safe_groups = []
    group_ids = set()
    for index, raw in enumerate(fixed.get("cardGroups", [])):
        if not isinstance(raw, dict):
            errors.append(
                _error(
                    "interaction_card_group_invalid",
                    "cardGroup 必须是对象，已移除。",
                )
            )
            continue
        group_id = str(raw.get("id") or f"card-group-{index + 1}")
        if group_id in group_ids:
            errors.append(
                _error(
                    "interaction_card_group_duplicate",
                    f"cardGroup {group_id} 重复，已移除。",
                    target=group_id,
                )
            )
            continue
        card_ids = [
            str(card_id)
            for card_id in raw.get("cardIds", [])
            if str(card_id) in layer_ids
            and layer_by_id[str(card_id)].get("type")
            in {"widget", "glassCard"}
        ]
        if not card_ids:
            errors.append(
                _error(
                    "interaction_card_group_empty",
                    f"cardGroup {group_id} 没有有效卡片，已移除。",
                    target=group_id,
                )
            )
            continue
        requested_index = int(raw.get("activeIndex") or 0)
        active_index = max(0, min(requested_index, len(card_ids) - 1))
        if card_ids != raw.get("cardIds") or active_index != requested_index:
            errors.append(
                _error(
                    "interaction_card_group_repaired",
                    f"cardGroup {group_id} 已修复。",
                    target=group_id,
                )
            )
        safe_groups.append(
            {
                "id": group_id,
                "cardIds": card_ids,
                "activeIndex": active_index,
                "loop": raw.get("loop") is not False,
                "transition": (
                    raw.get("transition")
                    if raw.get("transition") in {"slide", "fade"}
                    else "slide"
                ),
            }
        )
        group_ids.add(group_id)
    fixed["cardGroups"] = safe_groups

    safe_interactions = []
    used_ids = set()
    for index, raw in enumerate(fixed.get("interactions", [])):
        if not isinstance(raw, dict):
            errors.append(
                _error(
                    "interaction_invalid",
                    "interaction 必须是对象，已移除。",
                )
            )
            continue
        interaction_id = str(raw.get("id") or f"interaction-{index + 1}")
        target_id = str(raw.get("targetId") or "")
        if target_id not in layer_ids | group_ids:
            message = f"交互目标 {target_id or '(empty)'} 不存在，已移除。"
            errors.append(
                _error(
                    "interaction_target_missing",
                    message,
                    target=target_id,
                )
            )
            notices.append(_notice(target_id, message))
            continue
        trigger = normalize_trigger(raw.get("trigger"))
        if not trigger:
            errors.append(
                _error(
                    "interaction_trigger_invalid",
                    f"交互 {interaction_id} 的 trigger 无效，已移除。",
                    target=target_id,
                )
            )
            continue
        if trigger != raw.get("trigger"):
            errors.append(
                _error(
                    "interaction_trigger_repaired",
                    f"交互 {interaction_id} 的 trigger 参数已限制到安全范围。",
                    target=target_id,
                )
            )

        target_layer = layer_by_id.get(target_id, {})
        target_shape = str(target_layer.get("shape") or "")
        target = target_shape if target_shape in PARTICLE_SHAPES else ""
        actions = []
        for raw_action in raw.get("actions", []):
            action = normalize_action(raw_action, target)
            if not action:
                errors.append(
                    _error(
                        "interaction_action_invalid",
                        f"交互 {interaction_id} 包含无效 action，已移除。",
                        target=target_id,
                    )
                )
                continue
            if action["type"] == "burst":
                source = action["particleSource"]
                if source.get("type") == "asset":
                    material = get_asset(source.get("assetId"))
                    if not material:
                        action["particleSource"] = {
                            "type": "shape",
                            "shape": target or "circle",
                        }
                        errors.append(
                            _error(
                                "interaction_particle_untrusted",
                                f"交互 {interaction_id} 的粒子素材不可信，已降级为基础图形。",
                                target=target_id,
                            )
                        )
                    else:
                        action["particleSource"] = {
                            "type": "asset",
                            "assetId": material["assetId"],
                            "src": material.get("src")
                            or material.get("poster")
                            or "",
                        }
            if action != raw_action:
                errors.append(
                    _error(
                        "interaction_action_repaired",
                        f"交互 {interaction_id} 的 action 参数已规范化。",
                        target=target_id,
                    )
                )
            actions.append(action)
        if not actions:
            errors.append(
                _error(
                    "interaction_actions_empty",
                    f"交互 {interaction_id} 没有有效 action，已移除。",
                    target=target_id,
                )
            )
            continue
        if interaction_id in used_ids:
            suffix = 2
            base = interaction_id
            while f"{base}-{suffix}" in used_ids:
                suffix += 1
            interaction_id = f"{base}-{suffix}"
            errors.append(
                _error(
                    "interaction_id_duplicate",
                    "重复 interaction.id 已自动重命名。",
                    target=target_id,
                )
            )
        used_ids.add(interaction_id)
        safe_interactions.append(
            {
                "id": interaction_id,
                "targetId": target_id,
                "trigger": trigger,
                "actions": actions,
                "restart": (
                    "ignore"
                    if target_id in group_ids
                    else "restart"
                ),
            }
        )
    fixed["interactions"] = safe_interactions
    fixed["interactionNotices"] = [
        *(
            fixed.get("interactionNotices")
            if isinstance(fixed.get("interactionNotices"), list)
            else []
        ),
        *notices,
    ]
    return {
        "ok": True,
        "errors": errors,
        "notices": notices,
        "dsl": fixed,
    }
