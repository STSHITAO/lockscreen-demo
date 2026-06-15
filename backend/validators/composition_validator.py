import copy
from typing import Any

from utils.semantic_roles import excluded_semantic_roles, infer_semantic_role


SOURCE_PRIORITY = {
    "fallback": 0,
    "repair": 1,
    "draw-agent": 2,
    "material": 3,
    "model": 4,
    "user": 5,
    "system": 6,
}
UNIQUE_ROLES = {"time", "date", "weather", "schedule", "music"}
CARD_TYPES = {"widget", "glassCard"}


def _warning(issue_type: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "type": issue_type,
        "level": "warning",
        "message": message,
        **details,
    }


def _priority(layer: dict[str, Any]) -> int:
    return SOURCE_PRIORITY.get(str(layer.get("source") or "model"), 4)


def _normalize_sources(layers: list[dict[str, Any]]) -> None:
    for layer in layers:
        inferred_role = infer_semantic_role(layer)
        if inferred_role:
            layer["role"] = inferred_role
        source = str(layer.get("source") or "")
        if source in SOURCE_PRIORITY:
            continue
        layer["source"] = (
            "material"
            if layer.get("type") in {"asset", "frameAnimation"}
            else "model"
        )


def _in_bottom_card_region(layer: dict[str, Any]) -> bool:
    try:
        return float(layer.get("y") or 0) >= 600
    except (TypeError, ValueError):
        return False


def _deduplicate_roles(
    layers: list[dict[str, Any]],
    group_member_ids: set[str],
    warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    kept_layers = list(layers)
    for role in UNIQUE_ROLES:
        candidates = [
            layer for layer in kept_layers if layer.get("role") == role
        ]
        if len(candidates) <= 1:
            continue
        keep = max(
            candidates,
            key=lambda layer: (
                _priority(layer),
                str(layer.get("id")) in group_member_ids,
            ),
        )
        removed_ids = {
            str(layer["id"]) for layer in candidates if layer is not keep
        }
        kept_layers = [
            layer
            for layer in kept_layers
            if str(layer.get("id")) not in removed_ids
        ]
        warnings.append(
            _warning(
                "composition_slot_deduplicated",
                f"Duplicate {role} layers were reconciled by source priority.",
                role=role,
                keptLayerId=str(keep["id"]),
                removedLayerIds=sorted(removed_ids),
            )
        )
    return kept_layers


def _reconcile_card_groups(
    fixed: dict[str, Any],
    layers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    layer_by_id = {str(layer["id"]): layer for layer in layers}
    safe_groups = []
    owned_card_ids: set[str] = set()
    for raw_group in fixed.get("cardGroups", []):
        if not isinstance(raw_group, dict):
            continue
        group = copy.deepcopy(raw_group)
        card_ids = [
            str(card_id)
            for card_id in group.get("cardIds", [])
            if str(card_id) in layer_by_id
            and layer_by_id[str(card_id)].get("type") in CARD_TYPES
        ]
        group_roles = {
            str(layer_by_id[card_id].get("role") or "")
            for card_id in card_ids
            if layer_by_id[card_id].get("role")
        }
        for layer in layers:
            layer_id = str(layer["id"])
            role = str(layer.get("role") or "")
            if (
                layer_id in card_ids
                or layer_id in owned_card_ids
                or layer.get("type") not in CARD_TYPES
                or not _in_bottom_card_region(layer)
                or not role
                or role in group_roles
            ):
                continue
            card_ids.append(layer_id)
            group_roles.add(role)
            warnings.append(
                _warning(
                    "composition_card_adopted",
                    f"Bottom card {layer_id} was adopted by the card group.",
                    target=str(group.get("id") or ""),
                    layerId=layer_id,
                )
            )
        if card_ids:
            group["cardIds"] = card_ids
            group["activeIndex"] = max(
                0,
                min(int(group.get("activeIndex") or 0), len(card_ids) - 1),
            )
            safe_groups.append(group)
            owned_card_ids.update(card_ids)
    return safe_groups


def validate_composition(
    dsl: Any,
    prompt: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixed = copy.deepcopy(dsl) if isinstance(dsl, dict) else {"layers": []}
    layers = [
        layer
        for layer in fixed.get("layers", [])
        if isinstance(layer, dict) and layer.get("id")
    ]
    warnings: list[dict[str, Any]] = []
    _normalize_sources(layers)

    excluded_roles = excluded_semantic_roles(prompt)
    if excluded_roles:
        removed = [
            layer for layer in layers if layer.get("role") in excluded_roles
        ]
        if removed:
            layers = [
                layer
                for layer in layers
                if layer.get("role") not in excluded_roles
            ]
            warnings.append(
                _warning(
                    "composition_excluded_role_removed",
                    "Layers explicitly excluded by the user were removed.",
                    roles=sorted(excluded_roles),
                    layerIds=[str(layer["id"]) for layer in removed],
                )
            )

    if any(layer.get("source") != "fallback" for layer in layers):
        removed = [
            layer for layer in layers if layer.get("source") == "fallback"
        ]
        if removed:
            warnings.append(
                _warning(
                    "composition_fallback_removed",
                    "Generated content is available; global fallback layers were removed.",
                    layerIds=[str(layer["id"]) for layer in removed],
                )
            )
            layers = [
                layer for layer in layers if layer.get("source") != "fallback"
            ]

    group_member_ids = {
        str(card_id)
        for group in fixed.get("cardGroups", [])
        if isinstance(group, dict)
        for card_id in group.get("cardIds", [])
    }
    layers = _deduplicate_roles(layers, group_member_ids, warnings)
    fixed["layers"] = layers
    fixed["cardGroups"] = _reconcile_card_groups(fixed, layers, warnings)
    return {
        "ok": True,
        "errors": warnings,
        "notices": [],
        "dsl": fixed,
    }
