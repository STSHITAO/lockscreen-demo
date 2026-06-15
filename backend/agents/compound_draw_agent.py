import json
from typing import Any, Callable

import requests

from llm_client import (
    JSON_ONLY_RULES,
    _chat_completions_url,
    _request_model_json,
    _setting,
)
from utils.compound_shapes import normalize_compound_parts, safe_compound_id
from utils.shape_defaults import normalize_position_hint


COMPOUND_DRAW_SYSTEM_PROMPT = f"""
You create a simplified flat illustration plan for one missing visual object.
{JSON_ONLY_RULES}

Return an object with width, height, and parts. Use at most 24 parts.
Supported part shapes: circle, ellipse, rect, roundedRect, triangle, polygon,
line. Coordinates and sizes are normalized from 0 to 1. Triangle and polygon
parts use points such as [[0.1,0.8],[0.9,0.8],[0.5,0.1]]. Other parts use x,
y, width, and height. Optional fields are fill, stroke, strokeWidth, opacity,
rotation, and radius.

Create a recognizable simplified silhouette or flat icon. Prefer 6 to 16
parts. Preserve the requested color and defining features. Do not output SVG,
path data, HTML, CSS, code, explanations, or external assets.
""".strip()


def _number(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _position(
    hint: str,
    canvas_width: float,
    canvas_height: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    positions = {
        "top-left": (24, 72),
        "top-right": (canvas_width - width - 24, 72),
        "bottom-left": (24, canvas_height - height - 120),
        "bottom-right": (
            canvas_width - width - 24,
            canvas_height - height - 120,
        ),
        "bottom": ((canvas_width - width) / 2, canvas_height - height - 120),
        "around": (24, (canvas_height - height) / 2),
        "center": (
            (canvas_width - width) / 2,
            (canvas_height - height) / 2,
        ),
    }
    x, y = positions.get(hint, positions["center"])
    return round(max(0, x), 2), round(max(0, y), 2)


def _model_planner(request: dict[str, Any]) -> dict[str, Any]:
    api_key = _setting("LLM_API_KEY", "QWEN_API_KEY")
    base_url = _setting("LLM_BASE_URL", "QWEN_BASE_URL")
    model = _setting("LLM_MODEL", "QWEN_MODEL")
    if not api_key or not base_url or not model:
        raise RuntimeError("LLM configuration is incomplete")
    return _request_model_json(
        requester=requests.post,
        url=_chat_completions_url(base_url),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        model=model,
        system_prompt=COMPOUND_DRAW_SYSTEM_PROMPT,
        user_content=json.dumps(request, ensure_ascii=False),
        temperature=0.35,
    )


def create_compound_layer(
    target: str,
    position_hint: str | None,
    theme: str | None,
    canvas: dict[str, Any],
    *,
    planner: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    canvas_width = _number((canvas or {}).get("width"), 390)
    canvas_height = _number((canvas or {}).get("height"), 844)
    request = {
        "target": str(target or "").strip()[:120],
        "theme": str(theme or "custom")[:80],
        "position": normalize_position_hint(position_hint),
        "canvas": {"width": canvas_width, "height": canvas_height},
        "style": "recognizable simplified flat illustration or silhouette",
        "partBudget": 24,
    }
    plan = (planner or _model_planner)(request)
    parts = normalize_compound_parts(plan.get("parts"))
    if not parts:
        raise ValueError(f"Compound draw plan for {target} has no valid parts")

    width = max(48, min(_number(plan.get("width"), 168), 260))
    height = max(48, min(_number(plan.get("height"), 176), 300))
    hint = normalize_position_hint(position_hint)
    x, y = _position(
        hint,
        canvas_width,
        canvas_height,
        width,
        height,
    )
    return {
        "id": f"draw-{safe_compound_id(target)}",
        "type": "compoundShape",
        "target": str(target or "").strip().lower()[:120],
        "role": "decoration",
        "source": "draw-agent",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "opacity": 0.96,
        "parts": parts,
        "fallback": True,
        "fallbackReason": "asset_missing_compound_draw",
    }
