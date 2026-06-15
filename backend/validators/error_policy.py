from typing import Any


RENDERABLE_LAYER_TYPES = {
    "text",
    "widget",
    "shape",
    "glassCard",
    "asset",
    "frameAnimation",
    "compoundShape",
}


def is_recoverable_issue(issue: dict[str, Any]) -> bool:
    issue_type = str(issue.get("type") or "")
    return issue_type.startswith(("interaction_", "composition_"))


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
