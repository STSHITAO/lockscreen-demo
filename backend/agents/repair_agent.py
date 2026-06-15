import copy
import json
from typing import Any, Callable

import requests

from llm_client import (
    JSON_ONLY_RULES,
    _chat_completions_url,
    _request_model_json,
    _setting,
)
from material_catalog import get_asset, search_materials


REPAIR_SYSTEM_PROMPT = f"""
You repair an existing LockScreen DSL using a closed list of validation errors.
{JSON_ONLY_RULES}

Rules:
- Return the complete repaired LockScreen DSL JSON object.
- Change only fields needed to fix the supplied errors.
- Do not delete existing valid layers.
- Do not invent external image URLs, file paths, or asset IDs.
- Asset and frameAnimation layers may only use assetId values supplied in
  allowedAssetIds.
- Do not generate Vue, HTML, XML, SVG, markdown, or explanations.
""".strip()


def _find_layer(dsl: dict[str, Any], layer_id: str) -> dict[str, Any] | None:
    return next(
        (
            layer
            for layer in dsl.get("layers", [])
            if isinstance(layer, dict) and str(layer.get("id") or "") == layer_id
        ),
        None,
    )


def _position_layer(layer: dict[str, Any], region: str) -> None:
    width = float(layer.get("width") or 60)
    height = float(layer.get("height") or width)
    positions = {
        "top-left": (24, 64),
        "top-right": (390 - width - 24, 64),
        "bottom-left": (24, 844 - height - 24),
        "bottom-right": (390 - width - 24, 844 - height - 24),
        "bottom": ((390 - width) / 2, 844 - height - 34),
        "center": ((390 - width) / 2, (844 - height) / 2),
    }
    layer["x"], layer["y"] = positions.get(region, positions["center"])


def _add_weather(dsl: dict[str, Any]) -> None:
    if any(
        isinstance(layer, dict) and layer.get("role") == "weather"
        for layer in dsl["layers"]
    ):
        return
    dsl["layers"].append(
        {
            "id": "repair-weather",
            "type": "widget",
            "role": "weather",
            "source": "repair",
            "x": 32,
            "y": 690,
            "width": 326,
            "height": 104,
            "style": "glass",
            "content": {
                "title": "天气",
                "main": "天气信息",
                "icon": "",
            },
        }
    )


def _add_shape(dsl: dict[str, Any], target: str) -> None:
    if target == "moon":
        dsl["layers"].append(
            {
                "id": "moon",
                "type": "shape",
                "shape": "circle",
                "source": "repair",
                "x": 24,
                "y": 64,
                "width": 60,
                "height": 60,
                "color": "rgba(255,255,255,0.9)",
            }
        )
    elif target == "star":
        for index, (x, y) in enumerate(((48, 300), (320, 330), (72, 540)), 1):
            dsl["layers"].append(
                {
                    "id": f"star-{index}",
                    "type": "shape",
                    "shape": "star",
                    "source": "repair",
                    "x": x,
                    "y": y,
                    "width": 12,
                    "height": 12,
                    "color": "#ffffff",
                }
            )


def _add_catalog_asset(dsl: dict[str, Any], target: str) -> bool:
    matches = search_materials({"query": target}, limit=1)
    if not matches:
        return False
    material = matches[0]
    layer_type = (
        "frameAnimation"
        if material.get("assetType") == "frameSequence"
        else "asset"
    )
    layer = {
        "id": f"{target}-asset",
        "type": layer_type,
        "source": "material",
        "assetId": material["assetId"],
        "x": 270,
        "y": 64,
        "width": 90,
        "height": 90,
        "fit": "contain",
    }
    if layer_type == "frameAnimation":
        layer.update(
            {
                "frames": copy.deepcopy(material.get("frames") or []),
                "poster": material.get("poster"),
                "fps": material.get("fps", 6),
                "loop": material.get("loop", True),
                "frameCount": len(material.get("frames") or []),
            }
        )
        dsl["mode"] = "dynamic"
    else:
        layer["src"] = material["src"]
    dsl["layers"].append(layer)
    return True


def _repair_theme(dsl: dict[str, Any], target: str) -> None:
    backgrounds = {
        "night": "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
        "cute": "linear-gradient(180deg, #f9a8d4 0%, #db2777 100%)",
        "tech": "linear-gradient(180deg, #172554 0%, #020617 100%)",
    }
    dsl["theme"] = target
    dsl["background"] = {"type": "gradient", "value": backgrounds[target]}


def _program_repair(
    dsl: dict[str, Any],
    errors: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fixed = copy.deepcopy(dsl)
    fixed.setdefault("layers", [])
    unresolved = []

    for error in errors:
        error_type = error.get("type")
        target = str(error.get("target") or "")
        if error_type in {
            "schema_error",
            "layout_out_of_bounds",
            "layout_size_invalid",
            "safe_area_overlap",
            "asset_untrusted_src",
        }:
            continue
        if str(error_type or "").startswith("interaction_"):
            continue
        if error_type == "position_mismatch":
            layer = _find_layer(fixed, str(error.get("layerId") or ""))
            if layer:
                _position_layer(layer, str(error.get("expected") or "center"))
                continue
        if error_type == "semantic_missing":
            if target == "weather":
                _add_weather(fixed)
                continue
            if target in {"moon", "star"}:
                _add_shape(fixed, target)
                continue
            if target in {"night", "cute", "tech"}:
                _repair_theme(fixed, target)
                continue
            if target == "heart" and _add_catalog_asset(fixed, target):
                continue
        if error_type == "asset_missing" and target:
            material = get_asset(target)
            if material or _add_catalog_asset(fixed, target):
                continue
        unresolved.append(error)
    return fixed, unresolved


def _llm_repair(
    prompt: str,
    dsl: dict[str, Any],
    errors: list[dict[str, Any]],
    context: dict[str, Any],
    requester: Callable[..., Any],
) -> dict[str, Any]:
    api_key = _setting("LLM_API_KEY", "QWEN_API_KEY")
    base_url = _setting("LLM_BASE_URL", "QWEN_BASE_URL")
    model = _setting("LLM_MODEL", "QWEN_MODEL")
    if not api_key or not base_url or not model:
        return dsl

    safe_context = {
        "allowedAssetIds": context.get("allowedAssetIds", []),
        "intent": context.get("intent", {}),
    }
    return _request_model_json(
        requester=requester,
        url=_chat_completions_url(base_url),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        model=model,
        system_prompt=REPAIR_SYSTEM_PROMPT,
        user_content=json.dumps(
            {
                "userPrompt": prompt,
                "dsl": dsl,
                "errors": errors,
                "context": safe_context,
            },
            ensure_ascii=False,
        ),
        temperature=0.15,
    )


def _preserve_existing_structure(
    existing: dict[str, Any],
    repaired: dict[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(repaired) if isinstance(repaired, dict) else {}
    for field in ("layers", "cardGroups", "interactions"):
        original_items = (
            existing.get(field)
            if isinstance(existing.get(field), list)
            else []
        )
        repaired_items = (
            result.get(field)
            if isinstance(result.get(field), list)
            else []
        )
        merged = copy.deepcopy(repaired_items)
        existing_ids = {
            str(item.get("id") or "")
            for item in merged
            if isinstance(item, dict)
        }
        for item in original_items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "")
            if item_id and item_id not in existing_ids:
                merged.append(copy.deepcopy(item))
                existing_ids.add(item_id)
        result[field] = merged
    return result


def repair_dsl(
    prompt: str,
    dsl: dict[str, Any],
    errors: list[dict[str, Any]],
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    repair_context = context or {}
    fixed, unresolved = _program_repair(dsl, errors)
    if not unresolved:
        return fixed

    requester = repair_context.get("requester") or requests.post
    try:
        return _preserve_existing_structure(
            fixed,
            _llm_repair(
                prompt,
                fixed,
                unresolved,
                repair_context,
                requester=requester,
            ),
        )
    except Exception:
        return fixed
