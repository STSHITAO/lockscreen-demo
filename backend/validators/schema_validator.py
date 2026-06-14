import copy
from typing import Any


DEFAULT_CANVAS = {"width": 390, "height": 844}
DEFAULT_BACKGROUND = {
    "type": "gradient",
    "value": "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
}
BOX_DEFAULTS = {"x": 32, "y": 320, "width": 120, "height": 96}


def _error(field: str, message: str) -> dict[str, str]:
    return {
        "type": "schema_error",
        "level": "error",
        "field": field,
        "message": message,
    }


def _ensure_field(
    layer: dict[str, Any],
    field: str,
    default: Any,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    if field not in layer or layer[field] is None:
        layer[field] = copy.deepcopy(default)
        errors.append(_error(f"{path}.{field}", f"{path} 缺少 {field}"))


def validate_schema(dsl: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not isinstance(dsl, dict):
        errors.append(_error("$", "DSL 必须是 JSON 对象"))
        fixed: dict[str, Any] = {}
    else:
        fixed = copy.deepcopy(dsl)

    if not fixed.get("version"):
        fixed["version"] = "1.0"
        errors.append(_error("version", "DSL 缺少 version，已补为 1.0"))

    canvas = fixed.get("canvas")
    if not isinstance(canvas, dict):
        fixed["canvas"] = copy.deepcopy(DEFAULT_CANVAS)
        errors.append(_error("canvas", "DSL 缺少 canvas，已补为 390 × 844"))
    else:
        for field, default in DEFAULT_CANVAS.items():
            if not isinstance(canvas.get(field), (int, float)) or canvas[field] <= 0:
                canvas[field] = default
                errors.append(
                    _error(f"canvas.{field}", f"canvas.{field} 无效，已补为 {default}")
                )

    background = fixed.get("background")
    if not isinstance(background, dict):
        fixed["background"] = copy.deepcopy(DEFAULT_BACKGROUND)
        errors.append(_error("background", "DSL 缺少 background，已补默认渐变"))
    else:
        if background.get("type") not in {"gradient", "color"}:
            background["type"] = DEFAULT_BACKGROUND["type"]
            errors.append(_error("background.type", "background.type 无效"))
        if not background.get("value"):
            background["value"] = DEFAULT_BACKGROUND["value"]
            errors.append(_error("background.value", "background 缺少 value"))

    layers = fixed.get("layers")
    if not isinstance(layers, list):
        layers = []
        fixed["layers"] = layers
        errors.append(_error("layers", "layers 必须是数组"))

    safe_layers: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for index, raw_layer in enumerate(layers):
        path = f"layers[{index}]"
        if not isinstance(raw_layer, dict):
            errors.append(_error(path, "layer 必须是对象，已移除"))
            continue

        layer = copy.deepcopy(raw_layer)
        layer_id = str(layer.get("id") or f"layer-{index + 1}")
        if not layer.get("id"):
            errors.append(_error(f"{path}.id", "layer 缺少 id，已自动补全"))
        if layer_id in used_ids:
            base = layer_id
            suffix = 2
            while f"{base}-{suffix}" in used_ids:
                suffix += 1
            layer_id = f"{base}-{suffix}"
            errors.append(_error(f"{path}.id", "layer.id 重复，已自动重命名"))
        layer["id"] = layer_id
        used_ids.add(layer_id)

        layer_type = layer.get("type")
        if layer_type == "text":
            _ensure_field(layer, "content", "", path, errors)
            _ensure_field(layer, "x", 195, path, errors)
            _ensure_field(layer, "y", 320, path, errors)
        elif layer_type in {"widget", "glassCard"}:
            for field, default in BOX_DEFAULTS.items():
                _ensure_field(layer, field, default, path, errors)
        elif layer_type in {"asset", "frameAnimation"}:
            requires_asset_id = (
                layer_type == "frameAnimation" and not layer.get("assetId")
            )
            missing_static_source = (
                layer_type == "asset"
                and not layer.get("assetId")
                and not layer.get("src")
            )
            if requires_asset_id or missing_static_source:
                errors.append(
                    _error(
                        f"{path}.assetId",
                        f"{layer_type} layer 必须有 assetId",
                    )
                )
            for field, default in BOX_DEFAULTS.items():
                _ensure_field(layer, field, default, path, errors)
        elif layer_type == "shape":
            _ensure_field(layer, "shape", "roundedRect", path, errors)
            for field, default in BOX_DEFAULTS.items():
                _ensure_field(layer, field, default, path, errors)
        else:
            errors.append(_error(f"{path}.type", "不支持的 layer.type，已移除"))
            continue
        safe_layers.append(layer)

    fixed["layers"] = safe_layers
    fixed.setdefault("theme", "custom")
    fixed["mode"] = (
        "dynamic"
        if any(
            layer.get("type") == "frameAnimation" or layer.get("animation")
            for layer in safe_layers
        )
        or bool(fixed.get("interactions"))
        else "static"
    )
    return {"ok": not errors, "errors": errors, "dsl": fixed}
