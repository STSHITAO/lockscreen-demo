import copy
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

import requests
from dotenv import load_dotenv

from material_catalog import compact_material, get_asset, search_materials
from utils.animation_defaults import (
    SUPPORTED_ANIMATIONS,
    normalize_animation_requirements,
)
from utils.compound_shapes import normalize_compound_parts
from utils.interaction_defaults import normalize_interaction_requirements


logger = logging.getLogger(__name__)
ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=ENV_PATH)

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 300
ALLOWED_LAYER_TYPES = {
    "text",
    "widget",
    "shape",
    "glassCard",
    "asset",
    "frameAnimation",
    "compoundShape",
}
ALLOWED_SHAPES = {
    "circle",
    "roundedRect",
    "blob",
    "line",
    "star",
    "crescent",
    "heart",
    "cloud",
    "sparkle",
    "planet",
}
ALLOWED_ANIMATIONS = SUPPORTED_ANIMATIONS

FALLBACK_DSL = {
    "version": "1.0",
    "canvas": {"width": 390, "height": 844},
    "theme": "night",
    "mode": "static",
    "background": {
        "type": "gradient",
        "value": "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
    },
    "layers": [
        {
            "id": "ambient-glow",
            "type": "shape",
            "shape": "blob",
            "source": "fallback",
            "x": -70,
            "y": 420,
            "width": 270,
            "height": 270,
            "color": "rgba(56, 189, 248, 0.2)",
            "opacity": 0.75,
            "animation": "pulse",
        },
        {
            "id": "moon",
            "type": "shape",
            "shape": "circle",
            "source": "fallback",
            "x": 286,
            "y": 82,
            "width": 58,
            "height": 58,
            "color": "rgba(255,255,255,0.9)",
            "opacity": 0.92,
            "animation": "float",
        },
        {
            "id": "star-1",
            "type": "shape",
            "shape": "star",
            "source": "fallback",
            "x": 72,
            "y": 104,
            "width": 12,
            "height": 12,
            "color": "#f8fafc",
            "opacity": 0.85,
            "animation": "pulse",
        },
        {
            "id": "star-2",
            "type": "shape",
            "shape": "star",
            "source": "fallback",
            "x": 118,
            "y": 302,
            "width": 8,
            "height": 8,
            "color": "#bae6fd",
            "opacity": 0.7,
        },
        {
            "id": "star-3",
            "type": "shape",
            "shape": "star",
            "source": "fallback",
            "x": 320,
            "y": 282,
            "width": 10,
            "height": 10,
            "color": "#ffffff",
            "opacity": 0.78,
        },
    ],
}

JSON_ONLY_RULES = """
Output one JSON object only. Do not output explanations, markdown, code fences,
Vue, HTML, XML, or SVG. The complete response must be parseable by JSON.parse
and json.loads.
""".strip()

INTENT_SYSTEM_PROMPT = f"""
You extract a structured design brief and material search slots from a user's
lock-screen request. {JSON_ONLY_RULES}

Return:
{{
  "theme": "short theme",
  "moods": ["controlled English tags"],
  "colors": ["controlled English color tags"],
  "designBrief": "short composition direction",
  "animationRequirements": [
    {{
      "target": "object that should move",
      "motion": "float|pulse|rotate|twinkle|drift-left|drift-right|sway|bounce|fade|breathe, or a short description when complex",
      "complexity": "simple|complex",
      "preferredPosition": "center|top-left|top-right|bottom-left|bottom-right|around"
    }}
  ],
  "interactionRequirements": [
    {{
      "target": "visual object or card-group",
      "targetId": "optional preferred layer ID",
      "trigger": {{
        "type": "tap|multiTap|longPressStart|swipeLeft|swipeRight",
        "count": 3,
        "withinMs": 1200,
        "durationMs": 500
      }},
      "actions": [
        {{
          "type": "animate|stopAnimation|setAnimationSpeed|burst|switchCard|setVisibility|reset"
        }}
      ],
      "releaseActions": [],
      "complexity": "simple|complex"
    }}
  ],
  "assetSlots": [
    {{
      "slot": "hero|decoration|sticker",
      "query": "bilingual or English material search phrase",
      "subjects": ["concrete object tags"],
      "themes": ["theme tags"],
      "moods": ["mood tags"],
      "roles": ["hero|decoration|sticker|icon|callout"],
      "colors": ["color tags"],
      "preferredPosition": "center|bottom-center|top-left|top-right|bottom-left|bottom-right"
    }}
  ]
}}

Use at most three assetSlots: at most one hero and at most two decoration or
sticker slots. Create separate slots for separate requested objects. Do not
invent asset IDs or file paths. Use animationRequirements only when the user
explicitly asks for motion. Mark multi-stage transformations, character
performance, cinematic movement, or scene animation as complex.
Use interactionRequirements only when the user explicitly asks to tap,
multi-tap, long-press, release, or swipe. Preserve explicit tap counts; use
three for ambiguous repeated taps. Describe only controlled actions, never
JavaScript, CSS, event-handler code, or free SVG.
""".strip()

COMPOSITION_SYSTEM_PROMPT = f"""
You compose a premium 390 by 844 portrait phone lock screen from a design brief
and a closed list of local material candidates, including SVG assets and frame
sequences. {JSON_ONLY_RULES}

Return LockScreen DSL only. mode must be "dynamic" when a frameAnimation layer
is used; otherwise mode must be "static".
Supported layers:
- text: id, type, role, content, x, y, fontSize, fontWeight, color, align
- widget: id, type, role, x, y, width, height, style, content
- shape: id, type, shape, x, y, width, height, color, opacity, animation
- glassCard: id, type, role, x, y, width, height, content
- asset: id, type, assetId, x, y, width, height, fit, rotation, opacity,
  animation, effects
- frameAnimation: id, type, assetId, x, y, width, height, fit, rotation,
  opacity. Do not provide frames, poster, fps, or file paths; the backend fills
  those fields from the trusted animation catalog.
- compoundShape: id, type, target, x, y, width, height, opacity, parts. Each
  part uses only circle, ellipse, rect, roundedRect, triangle, polygon, or line
  with normalized 0..1 coordinates. Use at most 24 parts. Never output SVG
  paths, HTML, CSS, XML, or free-form drawing code.

Supported shapes: circle, roundedRect, blob, line, star, crescent, heart,
cloud, sparkle, planet.
Supported animations: float, pulse, rotate, twinkle, drift-left, drift-right,
sway, bounce, fade, breathe.
Optional top-level interaction fields:
- cardGroups: id, cardIds, activeIndex, loop, transition
- interactions: id, targetId, trigger, actions, restart
Supported triggers: tap, multiTap, longPressStart, longPressEnd, swipeLeft,
swipeRight.
Supported actions: animate, stopAnimation, setAnimationSpeed, burst,
switchCard, setVisibility, reset.
Interactions may reference only layer IDs and card-group IDs present in the
same DSL. Burst particles may use heart, star, sparkle, circle, or a supplied
trusted assetId. Never output JavaScript, CSS, handlers, or free SVG.
When animationRequirements are supplied, prefer a matching frameAnimation
candidate. If none exists and the requested motion is simple, use a supported
shape or static asset with the requested controlled animation. Do not attempt
complex animation using improvised layers.
For asset and frameAnimation layers, use only an assetId from the supplied
candidates and match the candidate assetType. Never write src, frames, URLs,
file paths, image, video, or lottie layers. Use at most one hero material and
two supporting materials. Preserve clear space for time/date, keep all layers
inside the canvas, and avoid covering the bottom home indicator.
""".strip()


def _setting(primary: str, alias: str) -> str:
    return (os.getenv(primary) or os.getenv(alias) or "").strip()


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _extract_balanced_object(content: str) -> str:
    start = content.find("{")
    if start < 0:
        raise ValueError("No JSON object found")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(content)):
        char = content[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]

    raise ValueError("Incomplete JSON object")


def parse_model_json(content: str) -> dict[str, Any]:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Empty model response")

    cleaned = content.strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = json.loads(_extract_balanced_object(cleaned))

    if not isinstance(parsed, dict):
        raise ValueError("Model response must be a JSON object")
    return parsed


def _number(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed == parsed else fallback
    except (TypeError, ValueError):
        return fallback


def _clamp(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    return max(minimum, min(_number(value, fallback), maximum))


def _string_list(value: Any, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def normalize_intent(candidate: dict[str, Any], prompt: str) -> dict[str, Any]:
    result = {
        "theme": str(candidate.get("theme") or "custom"),
        "moods": _string_list(candidate.get("moods")),
        "colors": _string_list(candidate.get("colors")),
        "designBrief": str(candidate.get("designBrief") or prompt).strip()[:600],
        "animationRequirements": normalize_animation_requirements(
            candidate.get("animationRequirements"),
            prompt,
        ),
        "interactionRequirements": normalize_interaction_requirements(
            candidate.get("interactionRequirements"),
            prompt,
        ),
        "assetSlots": [],
    }
    slots = candidate.get("assetSlots")
    if not isinstance(slots, list):
        return result

    hero_count = 0
    support_count = 0
    for raw_slot in slots:
        if not isinstance(raw_slot, dict):
            continue
        slot_type = str(raw_slot.get("slot") or "decoration")
        if slot_type == "hero":
            if hero_count >= 1:
                continue
            hero_count += 1
        else:
            slot_type = slot_type if slot_type in {"decoration", "sticker"} else "decoration"
            if support_count >= 2:
                continue
            support_count += 1

        subjects = _string_list(raw_slot.get("subjects"), 4)
        query = str(raw_slot.get("query") or " ".join(subjects)).strip()
        result["assetSlots"].append(
            {
                "slot": slot_type,
                "query": query[:200],
                "subjects": subjects,
                "themes": _string_list(raw_slot.get("themes")) or [result["theme"]],
                "moods": _string_list(raw_slot.get("moods")) or result["moods"],
                "roles": _string_list(raw_slot.get("roles"), 4) or [slot_type],
                "colors": _string_list(raw_slot.get("colors")) or result["colors"],
                "preferredPosition": str(
                    raw_slot.get("preferredPosition")
                    or ("center" if slot_type == "hero" else "top-right")
                ),
            }
        )
        if len(result["assetSlots"]) >= 3:
            break
    return result


def normalize_dsl(
    candidate: dict[str, Any],
    allowed_asset_ids: set[str] | None = None,
) -> dict[str, Any]:
    result = copy.deepcopy(candidate)
    result["version"] = str(result.get("version") or "1.0")
    result["canvas"] = {"width": 390, "height": 844}
    result["theme"] = str(result.get("theme") or "night")
    result["mode"] = "static"

    background = result.get("background")
    if not isinstance(background, dict):
        background = copy.deepcopy(FALLBACK_DSL["background"])
    background_type = background.get("type")
    if background_type not in {"gradient", "color"}:
        background = copy.deepcopy(FALLBACK_DSL["background"])
    background["value"] = str(
        background.get("value") or FALLBACK_DSL["background"]["value"]
    )
    result["background"] = background

    safe_layers = []
    layers = result.get("layers")
    if not isinstance(layers, list):
        raise ValueError("DSL layers must be an array")

    asset_count = 0
    used_assets: set[str] = set()
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict) or layer.get("type") not in ALLOWED_LAYER_TYPES:
            continue
        safe_layer = copy.deepcopy(layer)
        safe_layer["id"] = str(safe_layer.get("id") or f"layer-{index + 1}")
        if safe_layer.get("source") not in {
            "system",
            "user",
            "model",
            "material",
            "draw-agent",
            "repair",
            "fallback",
        }:
            safe_layer["source"] = (
                "material"
                if safe_layer["type"] in {"asset", "frameAnimation"}
                else "model"
            )
        if safe_layer["type"] == "shape":
            if safe_layer.get("shape") not in ALLOWED_SHAPES:
                continue
        if safe_layer["type"] == "compoundShape":
            parts = normalize_compound_parts(safe_layer.get("parts"))
            if not parts:
                continue
            width = _clamp(safe_layer.get("width"), 48, 260, 168)
            height = _clamp(safe_layer.get("height"), 48, 300, 176)
            safe_layer.update(
                {
                    "target": str(
                        safe_layer.get("target") or safe_layer["id"]
                    )[:120],
                    "x": _clamp(
                        safe_layer.get("x"),
                        0,
                        max(0, 390 - width),
                        111,
                    ),
                    "y": _clamp(
                        safe_layer.get("y"),
                        0,
                        max(0, 844 - height),
                        300,
                    ),
                    "width": width,
                    "height": height,
                    "opacity": _clamp(safe_layer.get("opacity"), 0, 1, 1),
                    "parts": parts,
                }
            )
        if safe_layer["type"] in {"asset", "frameAnimation"}:
            asset_id = str(safe_layer.get("assetId") or "")
            material = get_asset(asset_id)
            is_frame_sequence = (
                isinstance(material, dict)
                and material.get("assetType") == "frameSequence"
            )
            if (
                not material
                or asset_count >= 3
                or asset_id in used_assets
                or (allowed_asset_ids is not None and asset_id not in allowed_asset_ids)
                or (
                    safe_layer["type"] == "frameAnimation"
                    and not is_frame_sequence
                )
                or (safe_layer["type"] == "asset" and is_frame_sequence)
            ):
                continue
            width = _clamp(safe_layer.get("width"), 24, 390, 180)
            height = _clamp(safe_layer.get("height"), 24, 700, width)
            safe_layer.update(
                {
                    "assetId": asset_id,
                    "x": _clamp(safe_layer.get("x"), 0, max(0, 390 - width), 0),
                    "y": _clamp(safe_layer.get("y"), 0, max(0, 844 - height), 300),
                    "width": width,
                    "height": height,
                    "fit": safe_layer.get("fit")
                    if safe_layer.get("fit") in {"contain", "cover"}
                    else "contain",
                    "rotation": _clamp(safe_layer.get("rotation"), -180, 180, 0),
                    "opacity": _clamp(safe_layer.get("opacity"), 0, 1, 1),
                }
            )
            if safe_layer["type"] == "frameAnimation":
                safe_layer.update(
                    {
                        "frames": copy.deepcopy(material.get("frames") or []),
                        "poster": str(material.get("poster") or ""),
                        "fps": int(material.get("fps") or 6),
                        "loop": bool(material.get("loop", True)),
                        "frameCount": len(material.get("frames") or []),
                    }
                )
                safe_layer.pop("src", None)
                safe_layer.pop("animation", None)
                safe_layer.pop("effects", None)
            else:
                safe_layer["src"] = material["src"]
                if safe_layer.get("animation") not in ALLOWED_ANIMATIONS:
                    safe_layer.pop("animation", None)
                if not isinstance(safe_layer.get("effects"), dict):
                    safe_layer.pop("effects", None)
            asset_count += 1
            used_assets.add(asset_id)
        safe_layers.append(safe_layer)

    if not safe_layers:
        raise ValueError("DSL contains no supported layers")
    result["layers"] = safe_layers
    result.setdefault("cardGroups", [])
    result.setdefault("interactions", [])
    result.setdefault("interactionNotices", [])
    result["mode"] = (
        "dynamic"
        if any(
            layer.get("type") == "frameAnimation" or layer.get("animation")
            for layer in safe_layers
        )
        or bool(result["interactions"])
        else "static"
    )
    return result


def _request_model_json(
    *,
    requester: Callable[..., Any],
    url: str,
    headers: dict[str, str],
    model: str,
    system_prompt: str,
    user_content: str,
    temperature: float,
) -> dict[str, Any]:
    response = requester(
        url,
        headers=headers,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "enable_thinking": False,
        },
        timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
    )
    response.raise_for_status()
    data = response.json()
    return parse_model_json(data["choices"][0]["message"]["content"])


def _stream_request_model_json(
    *,
    requester: Callable[..., Any],
    url: str,
    headers: dict[str, str],
    model: str,
    system_prompt: str,
    user_content: str,
    temperature: float,
    phase: str,
):
    response = requester(
        url,
        headers=headers,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
            "stream": True,
            "stream_options": {"include_usage": True},
        },
        stream=True,
        timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
    )
    response.raise_for_status()

    content_parts: list[str] = []
    finish_reason = None
    output_chars = 0
    for raw_line in response.iter_lines(decode_unicode=True):
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode("utf-8", errors="replace")
        line = str(raw_line or "").strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        chunk = json.loads(payload)
        choices = chunk.get("choices") or []
        if not choices:
            continue
        choice = choices[0]
        delta = choice.get("delta") or {}
        reasoning = delta.get("reasoning_content") or ""
        if reasoning:
            yield {
                "type": "thinking",
                "phase": phase,
                "delta": reasoning,
            }
        content = delta.get("content") or ""
        if content:
            content_parts.append(content)
            output_chars += len(content)
            yield {
                "type": "progress",
                "phase": phase,
                "message": "正在生成结构化结果",
                "outputChars": output_chars,
            }
        if choice.get("finish_reason") is not None:
            finish_reason = choice["finish_reason"]

    if finish_reason is None:
        raise RuntimeError("Model stream closed without finish_reason")
    parsed = parse_model_json("".join(content_parts))
    yield {
        "type": "model_result",
        "phase": phase,
        "finishReason": finish_reason,
        "data": parsed,
    }


def _candidate_groups(intent: dict[str, Any]) -> list[dict[str, Any]]:
    groups = []
    for slot in intent.get("assetSlots", []):
        candidates = search_materials(slot, limit=5)
        groups.append(
            {
                "slot": slot["slot"],
                "preferredPosition": slot["preferredPosition"],
                "requirement": slot,
                "candidates": [compact_material(candidate) for candidate in candidates],
            }
        )
    return groups


def _fallback_with_materials(
    candidate_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    result = copy.deepcopy(FALLBACK_DSL)
    positions = {
        "hero": (75, 350, 240),
        "decoration": (270, 290, 88),
        "sticker": (32, 300, 96),
    }
    asset_layers = []
    for index, group in enumerate(candidate_groups[:3]):
        candidates = group.get("candidates") or []
        if not candidates:
            continue
        material = candidates[0]
        slot = group.get("slot") or "decoration"
        x, y, size = positions.get(slot, positions["decoration"])
        if index == 2 and slot != "hero":
            x = 28
            y = 530
        trusted = get_asset(material["assetId"])
        layer_type = (
            "frameAnimation"
            if trusted.get("assetType") == "frameSequence"
            else "asset"
        )
        layer = {
            "id": f"fallback-asset-{index + 1}",
            "type": layer_type,
            "assetId": material["assetId"],
            "x": x,
            "y": y,
            "width": size,
            "height": size,
            "fit": "contain",
            "rotation": -6 if index % 2 == 0 else 6,
            "opacity": 1,
            "source": "material",
        }
        if layer_type == "frameAnimation":
            layer.update(
                {
                    "frames": copy.deepcopy(trusted.get("frames") or []),
                    "poster": trusted.get("poster"),
                    "fps": trusted.get("fps", 6),
                    "loop": trusted.get("loop", True),
                    "frameCount": len(trusted.get("frames") or []),
                }
            )
            result["mode"] = "dynamic"
        else:
            layer["src"] = trusted["src"]
            layer["animation"] = "float" if slot == "hero" else "pulse"
        asset_layers.append(layer)
    first_text = next(
        (
            index
            for index, layer in enumerate(result["layers"])
            if layer.get("type") == "text"
        ),
        len(result["layers"]),
    )
    result["layers"][first_text:first_text] = asset_layers
    return result


def _local_prompt_candidates(prompt: str) -> list[dict[str, Any]]:
    candidates = search_materials({"query": prompt}, limit=1)
    if not candidates:
        return []
    return [
        {
            "slot": "hero",
            "preferredPosition": "center",
            "requirement": {"query": prompt, "roles": ["hero"]},
            "candidates": [compact_material(candidates[0])],
        }
    ]


def generate_lockscreen_dsl(
    prompt: str,
    requester: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    try:
        draft = generate_lockscreen_draft(prompt, requester=requester)
        return normalize_dsl(
            draft["dsl"],
            allowed_asset_ids=set(draft["context"]["allowedAssetIds"]),
        )
    except Exception as error:
        logger.warning("Lock-screen generation fell back: %s", error)
        return _fallback_with_materials(_local_prompt_candidates(prompt))


def generate_lockscreen_draft(
    prompt: str,
    requester: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    api_key = _setting("LLM_API_KEY", "QWEN_API_KEY")
    base_url = _setting("LLM_BASE_URL", "QWEN_BASE_URL")
    model = _setting("LLM_MODEL", "QWEN_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError("LLM configuration is incomplete")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = _chat_completions_url(base_url)
    raw_intent = _request_model_json(
        requester=requester,
        url=url,
        headers=headers,
        model=model,
        system_prompt=INTENT_SYSTEM_PROMPT,
        user_content=prompt.strip(),
        temperature=0.2,
    )
    intent = normalize_intent(raw_intent, prompt)
    candidate_groups = _candidate_groups(intent)
    composition_input = json.dumps(
        {
            "userPrompt": prompt.strip(),
            "designBrief": intent,
            "materialCandidateGroups": candidate_groups,
        },
        ensure_ascii=False,
    )
    raw_dsl = _request_model_json(
        requester=requester,
        url=url,
        headers=headers,
        model=model,
        system_prompt=COMPOSITION_SYSTEM_PROMPT,
        user_content=composition_input,
        temperature=0.65,
    )
    allowed_asset_ids = {
        candidate["assetId"]
        for group in candidate_groups
        for candidate in group["candidates"]
    }
    return {
        "dsl": raw_dsl,
        "context": {
            "intent": intent,
            "materialCandidateGroups": candidate_groups,
            "allowedAssetIds": sorted(allowed_asset_ids),
        },
    }


def generate_lockscreen_draft_stream(
    prompt: str,
    requester: Callable[..., Any] = requests.post,
):
    api_key = _setting("LLM_API_KEY", "QWEN_API_KEY")
    base_url = _setting("LLM_BASE_URL", "QWEN_BASE_URL")
    model = _setting("LLM_MODEL", "QWEN_MODEL")
    if not api_key or not base_url or not model:
        raise RuntimeError("LLM configuration is incomplete")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = _chat_completions_url(base_url)

    yield {
        "type": "phase",
        "phase": "intent",
        "status": "running",
        "label": "理解需求",
    }
    intent = None
    for event in _stream_request_model_json(
        requester=requester,
        url=url,
        headers=headers,
        model=model,
        system_prompt=INTENT_SYSTEM_PROMPT,
        user_content=prompt.strip(),
        temperature=0.2,
        phase="intent",
    ):
        if event["type"] == "model_result":
            intent = normalize_intent(event["data"], prompt)
        else:
            yield event
    if intent is None:
        raise RuntimeError("Intent stream produced no result")
    yield {
        "type": "phase",
        "phase": "intent",
        "status": "done",
        "label": "需求理解完成",
    }

    yield {
        "type": "phase",
        "phase": "materials",
        "status": "running",
        "label": "检索本地素材",
    }
    candidate_groups = _candidate_groups(intent)
    candidate_count = sum(len(group["candidates"]) for group in candidate_groups)
    yield {
        "type": "phase",
        "phase": "materials",
        "status": "done",
        "label": f"找到 {candidate_count} 个候选素材",
        "candidateCount": candidate_count,
    }

    composition_input = json.dumps(
        {
            "userPrompt": prompt.strip(),
            "designBrief": intent,
            "materialCandidateGroups": candidate_groups,
        },
        ensure_ascii=False,
    )
    yield {
        "type": "phase",
        "phase": "composition",
        "status": "running",
        "label": "设计锁屏布局",
    }
    raw_dsl = None
    for event in _stream_request_model_json(
        requester=requester,
        url=url,
        headers=headers,
        model=model,
        system_prompt=COMPOSITION_SYSTEM_PROMPT,
        user_content=composition_input,
        temperature=0.65,
        phase="composition",
    ):
        if event["type"] == "model_result":
            raw_dsl = event["data"]
        else:
            yield event
    if raw_dsl is None:
        raise RuntimeError("Composition stream produced no result")
    yield {
        "type": "phase",
        "phase": "composition",
        "status": "done",
        "label": "DSL 初稿生成完成",
    }

    allowed_asset_ids = {
        candidate["assetId"]
        for group in candidate_groups
        for candidate in group["candidates"]
    }
    yield {
        "type": "draft_result",
        "dsl": raw_dsl,
        "context": {
            "intent": intent,
            "materialCandidateGroups": candidate_groups,
            "allowedAssetIds": sorted(allowed_asset_ids),
        },
    }
