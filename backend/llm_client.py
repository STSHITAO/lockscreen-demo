import copy
import json
import os
from pathlib import Path
from typing import Any, Callable

import requests
from dotenv import load_dotenv


ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=ENV_PATH)

ALLOWED_LAYER_TYPES = {"text", "widget", "shape", "glassCard"}
ALLOWED_SHAPES = {"circle", "roundedRect", "blob", "line", "star"}

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
            "x": 320,
            "y": 282,
            "width": 10,
            "height": 10,
            "color": "#ffffff",
            "opacity": 0.78,
        },
        {
            "id": "time",
            "type": "text",
            "role": "time",
            "content": "18:30",
            "x": 195,
            "y": 176,
            "fontSize": 76,
            "fontWeight": 750,
            "color": "#ffffff",
            "align": "center",
        },
        {
            "id": "date",
            "type": "text",
            "role": "date",
            "content": "Thursday, June 11",
            "x": 195,
            "y": 248,
            "fontSize": 18,
            "fontWeight": 450,
            "color": "rgba(255,255,255,0.78)",
            "align": "center",
        },
        {
            "id": "weather",
            "type": "widget",
            "role": "weather",
            "x": 32,
            "y": 690,
            "width": 326,
            "height": 104,
            "style": "glass",
            "content": {
                "title": "今日天气",
                "main": "26°C · Cloudy",
                "icon": "☁",
            },
        },
    ],
}

SYSTEM_PROMPT = """
You are a lock-screen visual DSL generator. Convert the user's natural-language
request into one LockScreen DSL JSON object.

Output rules:
- Output JSON only.
- Do not output explanations, markdown, or code fences.
- The complete response must be parseable by JSON.parse and json.loads.
- Output a JSON object, never an array.
- Generate LockScreen DSL only. Do not generate Vue, HTML, XML, or SVG.
- Canvas must be 390 by 844.
- mode must be "static".
- Use only CSS colors and gradients. Never use image, video, lottie, URLs, files,
  materials, or external assets.

Supported layer types:
- text: id, type, role, content, x, y, fontSize, fontWeight, color, align
- widget: id, type, role, x, y, width, height, style, content
- shape: id, type, shape, x, y, width, height, color, opacity, animation
- glassCard: id, type, role, x, y, width, height, content

Supported shapes: circle, roundedRect, blob, line, star.
Supported animations: float, pulse, rotate.
widget/glassCard content should be an object with short title, main, optional
subtitle, and optional icon fields. Keep every layer inside the canvas and make
the result look like a premium portrait phone lock screen.
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


def normalize_dsl(candidate: dict[str, Any]) -> dict[str, Any]:
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

    for index, layer in enumerate(layers):
        if not isinstance(layer, dict) or layer.get("type") not in ALLOWED_LAYER_TYPES:
            continue
        safe_layer = copy.deepcopy(layer)
        safe_layer["id"] = str(safe_layer.get("id") or f"layer-{index + 1}")
        if safe_layer["type"] == "shape":
            if safe_layer.get("shape") not in ALLOWED_SHAPES:
                continue
        safe_layers.append(safe_layer)

    if not safe_layers:
        raise ValueError("DSL contains no supported layers")
    result["layers"] = safe_layers
    return result


def generate_lockscreen_dsl(
    prompt: str,
    requester: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    api_key = _setting("LLM_API_KEY", "QWEN_API_KEY")
    base_url = _setting("LLM_BASE_URL", "QWEN_BASE_URL")
    model = _setting("LLM_MODEL", "QWEN_MODEL")

    if not api_key or not base_url or not model:
        return copy.deepcopy(FALLBACK_DSL)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt.strip()},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requester(
            _chat_completions_url(base_url),
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return normalize_dsl(parse_model_json(content))
    except Exception:
        return copy.deepcopy(FALLBACK_DSL)
