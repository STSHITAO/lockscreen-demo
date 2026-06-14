import copy
from typing import Any
from urllib.parse import urlparse

from material_catalog import get_asset, load_materials
from utils.shape_defaults import (
    normalize_target,
    shape_satisfies_target,
    target_aliases,
)


def _asset_error(
    *,
    target: str,
    layer_id: str,
    message: str,
) -> dict[str, str]:
    return {
        "type": "asset_missing",
        "level": "error",
        "target": target,
        "layerId": layer_id,
        "message": message,
    }


def _is_external_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} or str(value or "").startswith("//")


def _dsl_satisfies_target(layers: list[Any], target: str) -> bool:
    normalized = normalize_target(target) or str(target or "").strip().lower()
    aliases = set(target_aliases(normalized))

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        if shape_satisfies_target(layer, normalized):
            return True
        values = {
            str(layer.get("id") or "").lower(),
            str(layer.get("role") or "").lower(),
            str(layer.get("shape") or "").lower(),
            str(layer.get("target") or "").lower(),
        }
        material = get_asset(str(layer.get("assetId") or ""))
        if material:
            values.update(str(value).lower() for value in material.get("subjects") or [])
            values.update(str(value).lower() for value in material.get("keywords") or [])
        if any(alias in value for alias in aliases for value in values):
            return True
    return False


def _target_requested(prompt: str, target: str, requirement: dict[str, Any]) -> bool:
    text = str(prompt or "").lower()
    normalized = normalize_target(target) or str(target or "").lower()
    aliases = set(target_aliases(normalized))
    terms = {
        str(requirement.get("query") or "").lower(),
        *(str(value).lower() for value in requirement.get("subjects") or []),
    }
    terms.update(aliases)
    return any(term and term in text for term in terms)


def validate_assets(
    dsl: Any,
    prompt: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixed = copy.deepcopy(dsl) if isinstance(dsl, dict) else {"layers": []}
    layers = fixed.get("layers") if isinstance(fixed.get("layers"), list) else []
    errors: list[dict[str, str]] = []
    by_src = {
        asset["src"]: asset
        for asset in load_materials()
        if asset.get("src")
    }
    safe_layers = []

    for layer in layers:
        if (
            not isinstance(layer, dict)
            or layer.get("type") not in {"asset", "frameAnimation"}
        ):
            safe_layers.append(layer)
            continue

        layer_id = str(layer.get("id") or "asset")
        layer_type = str(layer.get("type") or "")
        asset_id = str(layer.get("assetId") or "")
        material = get_asset(asset_id) if asset_id else None
        if (
            layer_type == "asset"
            and not material
            and not asset_id
            and not _is_external_url(layer.get("src"))
        ):
            material = by_src.get(str(layer.get("src") or ""))
            if material:
                layer["assetId"] = material["assetId"]

        if not material:
            target = asset_id or layer_id
            errors.append(
                _asset_error(
                    target=target,
                    layer_id=layer_id,
                    message=f"素材库中不存在可信 asset：{target}",
                )
            )
            continue

        is_frame_sequence = material.get("assetType") == "frameSequence"
        if layer_type == "frameAnimation" and not is_frame_sequence:
            errors.append(
                _asset_error(
                    target=asset_id,
                    layer_id=layer_id,
                    message=f"{asset_id} 不是序列帧动画素材",
                )
            )
            continue
        if layer_type == "asset" and is_frame_sequence:
            errors.append(
                _asset_error(
                    target=asset_id,
                    layer_id=layer_id,
                    message=f"{asset_id} 必须使用 frameAnimation layer",
                )
            )
            continue

        if layer_type == "frameAnimation":
            layer["frames"] = copy.deepcopy(material.get("frames") or [])
            layer["poster"] = str(material.get("poster") or "")
            layer["fps"] = int(material.get("fps") or 6)
            layer["loop"] = bool(material.get("loop", True))
            layer["frameCount"] = len(layer["frames"])
            safe_layers.append(layer)
            continue

        if _is_external_url(layer.get("src")):
            errors.append(
                {
                    "type": "asset_untrusted_src",
                    "level": "error",
                    "target": material["assetId"],
                    "layerId": layer_id,
                    "message": "asset src 不允许使用外部 URL，已替换为本地素材路径",
                }
            )
        layer["src"] = material["src"]
        safe_layers.append(layer)

    fixed["layers"] = safe_layers
    fixed["mode"] = (
        "dynamic"
        if any(
            isinstance(layer, dict)
            and (
                layer.get("type") == "frameAnimation"
                or layer.get("animation")
            )
            for layer in safe_layers
        )
        else "static"
    )
    for group in (context or {}).get("materialCandidateGroups", []):
        if isinstance(group, dict) and not group.get("candidates"):
            requirement = group.get("requirement") or {}
            target = (
                next(iter(requirement.get("subjects") or []), "")
                or requirement.get("query")
                or group.get("slot")
                or "asset"
            )
            unavailable = {
                str(value).strip().lower()
                for value in (context or {}).get("unavailableVisuals", [])
            }
            if str(target).strip().lower() in unavailable:
                continue
            if not _target_requested(prompt, str(target), requirement):
                continue
            if _dsl_satisfies_target(safe_layers, str(target)):
                continue
            errors.append(
                _asset_error(
                    target=str(target),
                    layer_id="",
                    message=f"用户需要 {target}，但素材库中没有可信候选",
                )
            )

    return {"ok": not errors, "errors": errors, "dsl": fixed}
