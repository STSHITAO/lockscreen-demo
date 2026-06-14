from typing import Any


RENDERABLE_LAYER_TYPES = {
    "text",
    "widget",
    "shape",
    "glassCard",
    "asset",
    "frameAnimation",
}


def is_recoverable_issue(issue: dict[str, Any]) -> bool:
    return str(issue.get("type") or "").startswith("interaction_")


def is_renderable_dsl(dsl: Any) -> bool:
    if not isinstance(dsl, dict):
        return False
    layers = dsl.get("layers")
    if not isinstance(layers, list):
        return False
    return any(
        isinstance(layer, dict)
        and layer.get("type") in RENDERABLE_LAYER_TYPES
        and layer.get("id")
        for layer in layers
    )
