import copy
from typing import Any

from agents.fallback_draw_agent import create_fallback_layer
from material_catalog import get_asset, search_materials
from utils.animation_defaults import normalize_animation_requirements
from utils.shape_defaults import normalize_target
from validators.layout_validator import find_target_layers


def _notice(target: str, motion: str) -> dict[str, str]:
    return {
        "type": "animation_unavailable",
        "level": "warning",
        "target": target,
        "motion": motion,
        "message": (
            f'\u672a\u5339\u914d\u5230\u201c{target}\u201d\u7684\u52a8\u753b\u7d20\u6750\uff0c'
            "\u8be5\u52a8\u753b\u6548\u679c\u8f83\u590d\u6742\uff0c"
            "\u6682\u65f6\u65e0\u6cd5\u81ea\u4e3b\u751f\u6210\u3002"
        ),
    }


def _matching_frame_material(
    context: dict[str, Any],
    target: str,
    motion: str,
) -> dict[str, Any] | None:
    candidate_ids = []
    for group in context.get("materialCandidateGroups", []):
        if not isinstance(group, dict):
            continue
        requirement = (
            group.get("requirement")
            if isinstance(group.get("requirement"), dict)
            else {}
        )
        requirement_targets = {
            normalize_target(value)
            for value in [
                *(requirement.get("subjects") or []),
                requirement.get("query"),
            ]
        }
        if target not in requirement_targets:
            continue
        candidate_ids.extend(
            candidate.get("assetId")
            for candidate in group.get("candidates", [])
            if isinstance(candidate, dict)
        )

    searched = search_materials(
        {"subjects": [target], "query": f"{target} {motion}"},
        limit=5,
    )
    candidate_ids.extend(material.get("assetId") for material in searched)

    for asset_id in dict.fromkeys(candidate_ids):
        material = get_asset(str(asset_id or ""))
        if (
            material
            and material.get("assetType") == "frameSequence"
            and target in {
                normalize_target(subject)
                for subject in material.get("subjects", [])
            }
        ):
            return material
    return None


def _frame_layer(
    material: dict[str, Any],
    target: str,
    position_hint: str | None,
    theme: str,
    canvas: dict[str, Any],
) -> dict[str, Any]:
    anchor = create_fallback_layer(
        target,
        position_hint,
        theme,
        canvas,
    )
    size = 88
    anchor_width = float(anchor.get("width") or size)
    anchor_height = float(anchor.get("height") or size)
    x = float(anchor.get("x") or 0) + (anchor_width - size) / 2
    y = float(anchor.get("y") or 0) + (anchor_height - size) / 2
    canvas_width = float(canvas.get("width") or 390)
    canvas_height = float(canvas.get("height") or 844)
    frames = copy.deepcopy(material.get("frames") or [])
    return {
        "id": f"frame_{target}_{material['assetId']}",
        "type": "frameAnimation",
        "assetId": material["assetId"],
        "target": target,
        "role": "decoration",
        "x": max(0, min(x, canvas_width - size)),
        "y": max(0, min(y, canvas_height - size)),
        "width": size,
        "height": size,
        "fit": "contain",
        "opacity": 1,
        "frames": frames,
        "poster": material.get("poster") or (frames[0] if frames else ""),
        "fps": material.get("fps", 6),
        "loop": material.get("loop", True),
        "frameCount": len(frames),
    }


def apply_animation_fallbacks(
    dsl: dict[str, Any],
    prompt: str,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    current = copy.deepcopy(dsl)
    current.setdefault("layers", [])
    animation_context = context or {}
    intent = (
        animation_context.get("intent")
        if isinstance(animation_context.get("intent"), dict)
        else {}
    )
    requirements = normalize_animation_requirements(
        intent.get("animationRequirements"),
        prompt,
    )
    applied = []
    notices = []
    canvas = current.get("canvas") or {"width": 390, "height": 844}
    theme = str(current.get("theme") or "")

    for requirement in requirements:
        target = requirement["target"]
        motion = requirement["motion"]
        if requirement["complexity"] == "complex":
            notices.append(_notice(target, motion))
            continue

        matching_layers = find_target_layers(current, target)
        if any(layer.get("type") == "frameAnimation" for layer in matching_layers):
            continue

        frame_material = _matching_frame_material(
            animation_context,
            target,
            motion,
        )
        if frame_material:
            existing_frame = next(
                (
                    layer
                    for layer in current["layers"]
                    if layer.get("type") == "frameAnimation"
                    and layer.get("assetId") == frame_material.get("assetId")
                ),
                None,
            )
            layer = existing_frame or _frame_layer(
                frame_material,
                target,
                requirement.get("preferredPosition"),
                theme,
                canvas,
            )
            if existing_frame is None:
                current["layers"].append(layer)
            applied.append(
                {
                    "target": target,
                    "motion": "frame-sequence",
                    "layerId": str(layer.get("id") or ""),
                }
            )
            continue

        if matching_layers:
            layer = matching_layers[0]
            layer["animation"] = motion
        else:
            canonical = normalize_target(target)
            if not canonical:
                notices.append(_notice(target, motion))
                continue
            layer = create_fallback_layer(
                canonical,
                requirement.get("preferredPosition"),
                theme,
                canvas,
            )
            layer["animation"] = motion
            layer["fallbackReason"] = "animation_asset_missing"
            current["layers"].append(layer)

        applied.append(
            {
                "target": target,
                "motion": motion,
                "layerId": str(layer.get("id") or ""),
            }
        )

    if applied or any(
        layer.get("type") == "frameAnimation"
        for layer in current.get("layers", [])
        if isinstance(layer, dict)
    ):
        current["mode"] = "dynamic"

    return {
        "dsl": current,
        "applied": applied,
        "notices": notices,
        "requirements": requirements,
    }
