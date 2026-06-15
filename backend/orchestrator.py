import copy
from typing import Any, Callable

from agents.animation_fallback_agent import apply_animation_fallbacks
from agents.compound_draw_agent import create_compound_layer
from agents.fallback_draw_agent import create_fallback_layer
from agents.interaction_agent import apply_interaction_requirements
from agents.repair_agent import repair_dsl
from llm_client import (
    FALLBACK_DSL,
    generate_lockscreen_draft,
    generate_lockscreen_draft_stream,
)
from material_catalog import search_materials
from validators import (
    validate_assets,
    validate_composition,
    validate_interactions,
    validate_layout,
    validate_schema,
    validate_semantics,
)
from validators.error_policy import is_recoverable_issue, is_renderable_dsl
from utils.shape_defaults import infer_position_hint, normalize_target


MAX_REPAIR_ROUNDS = 2
FALLBACK_ERROR_TYPES = {
    "asset_missing",
    "required_visual_missing",
    "semantic_missing",
}


def _should_draw_fallback(error: dict[str, Any], target: str) -> bool:
    error_type = error.get("type")
    if error_type == "required_visual_missing":
        return True
    if error_type == "asset_missing" and not error.get("layerId"):
        return True
    return not search_materials({"query": target}, limit=1)


def _inject_fallback_layers(
    dsl: dict[str, Any],
    errors: list[dict[str, Any]],
    prompt: str,
    context: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    current = copy.deepcopy(dsl)
    layers = current.setdefault("layers", [])
    canvas = current.get("canvas") or {"width": 390, "height": 844}
    theme = current.get("theme")
    existing_ids = {
        str(layer.get("id") or "")
        for layer in layers
        if isinstance(layer, dict)
    }
    added: list[dict[str, Any]] = []
    handled_targets: set[str] = set()

    for error in errors:
        if error.get("type") not in FALLBACK_ERROR_TYPES:
            continue
        raw_target = str(error.get("target") or "").strip()
        target = normalize_target(raw_target)
        target_key = target or raw_target.lower()
        if not target_key or target_key in handled_targets:
            continue
        if not _should_draw_fallback(error, target or raw_target):
            continue
        requirement = next(
            (
                group.get("requirement") or {}
                for group in context.get("materialCandidateGroups", [])
                if isinstance(group, dict)
                and raw_target.lower()
                in {
                    str(value).strip().lower()
                    for value in (
                        (group.get("requirement") or {}).get("subjects") or []
                    )
                }
            ),
            {},
        )
        position_hint = (
            error.get("expected")
            or requirement.get("preferredPosition")
            or infer_position_hint(prompt, target or raw_target)
            or "center"
        )
        try:
            if target:
                layer = create_fallback_layer(
                    target,
                    str(position_hint),
                    str(theme or ""),
                    canvas,
                )
            else:
                layer = create_compound_layer(
                    raw_target,
                    str(position_hint),
                    str(theme or ""),
                    canvas,
                    planner=context.get("compoundPlanner"),
                )
        except (RuntimeError, TypeError, ValueError):
            continue
        base_id = layer["id"]
        suffix = 2
        while layer["id"] in existing_ids:
            layer["id"] = f"{base_id}-{suffix}"
            suffix += 1
        existing_ids.add(layer["id"])
        layers.append(layer)
        added.append(copy.deepcopy(layer))
        handled_targets.add(target_key)

    return current, added


def _run_animation_stage(
    validation: dict[str, Any],
    prompt: str,
    context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    animation_result = apply_animation_fallbacks(
        validation["dsl"],
        prompt,
        context,
    )
    notices = animation_result["notices"]
    context["animationNotices"] = copy.deepcopy(notices)
    context["unavailableVisuals"] = [
        notice["target"] for notice in notices if notice.get("target")
    ]
    if animation_result["applied"] or notices:
        validation = _run_validators(
            animation_result["dsl"],
            prompt,
            context,
        )
    return validation, animation_result


def _run_interaction_stage(
    validation: dict[str, Any],
    prompt: str,
    context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    interaction_result = apply_interaction_requirements(
        validation["dsl"],
        prompt,
        context,
    )
    notices = interaction_result["notices"]
    existing_notices = context.setdefault("interactionNotices", [])
    for notice in notices:
        if notice not in existing_notices:
            existing_notices.append(copy.deepcopy(notice))
    if interaction_result["applied"] or notices:
        validation = _run_validators(
            interaction_result["dsl"],
            prompt,
            context,
        )
    return validation, interaction_result


def _run_validators(
    dsl: Any,
    prompt: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    current = copy.deepcopy(dsl)
    errors: list[dict[str, Any]] = []
    validators = (
        lambda value: validate_schema(value),
        lambda value: validate_assets(value, prompt, context),
        lambda value: validate_layout(value, prompt, context),
        lambda value: validate_semantics(value, prompt, context),
        lambda value: validate_composition(value, prompt, context),
        lambda value: validate_interactions(value, prompt, context),
    )
    for validator in validators:
        result = validator(current)
        current = result["dsl"]
        errors.extend(
            error
            for error in result["errors"]
            if not is_recoverable_issue(error)
        )
        for notice in result.get("notices", []):
            if notice not in context.setdefault("interactionNotices", []):
                context["interactionNotices"].append(copy.deepcopy(notice))
    return {"ok": not errors, "errors": errors, "dsl": current}


def _with_debug(
    dsl: dict[str, Any],
    *,
    loop_count: int,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    used_fallback: bool,
    animation_notices: list[dict[str, Any]] | None = None,
    interaction_notices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = copy.deepcopy(dsl)
    result["_debug"] = {
        "loopCount": loop_count,
        "errorsBeforeRepair": copy.deepcopy(before),
        "errorsAfterRepair": copy.deepcopy(after),
        "usedFallback": used_fallback,
        "animationNotices": copy.deepcopy(animation_notices or []),
        "interactionNotices": copy.deepcopy(interaction_notices or []),
    }
    return result


def _default_draft_generator(prompt: str) -> dict[str, Any]:
    return generate_lockscreen_draft(prompt)


def generate_lockscreen_with_agent_loop(
    prompt: str,
    *,
    draft_generator: Callable[[str], Any] = _default_draft_generator,
    repairer: Callable[
        [str, dict[str, Any], list[dict[str, Any]], dict[str, Any]],
        dict[str, Any],
    ] = repair_dsl,
    max_repairs: int = MAX_REPAIR_ROUNDS,
) -> dict[str, Any]:
    try:
        generated = draft_generator(prompt)
        if (
            isinstance(generated, dict)
            and isinstance(generated.get("dsl"), dict)
            and isinstance(generated.get("context"), dict)
        ):
            draft = generated["dsl"]
            context = generated["context"]
        else:
            draft = generated
            context = {}
    except Exception as error:
        generation_error = [
            {
                "type": "generation_error",
                "level": "error",
                "message": str(error),
            }
        ]
        return _with_debug(
            FALLBACK_DSL,
            loop_count=0,
            before=generation_error,
            after=generation_error,
            used_fallback=True,
            animation_notices=[],
            interaction_notices=[],
        )

    validation = _run_validators(draft, prompt, context)
    errors_before = copy.deepcopy(validation["errors"])
    validation, animation_result = _run_animation_stage(
        validation,
        prompt,
        context,
    )
    validation, interaction_result = _run_interaction_stage(
        validation,
        prompt,
        context,
    )
    fallback_dsl, fallback_layers = _inject_fallback_layers(
        validation["dsl"],
        validation["errors"],
        prompt,
        context,
    )
    if fallback_layers:
        validation = _run_validators(fallback_dsl, prompt, context)
    if validation["ok"]:
        return _with_debug(
            validation["dsl"],
            loop_count=0,
            before=[],
            after=[],
            used_fallback=False,
            animation_notices=context.get("animationNotices", []),
            interaction_notices=context.get("interactionNotices", []),
        )

    current = validation["dsl"]
    current_errors = validation["errors"]
    repair_limit = max(0, min(int(max_repairs), MAX_REPAIR_ROUNDS))
    for loop_count in range(1, repair_limit + 1):
        try:
            current = repairer(prompt, current, current_errors, context)
        except Exception:
            current = validation["dsl"]
        validation = _run_validators(current, prompt, context)
        current = validation["dsl"]
        current_errors = validation["errors"]
        if validation["ok"]:
            return _with_debug(
                current,
                loop_count=loop_count,
                before=errors_before,
                after=[],
                used_fallback=False,
                animation_notices=context.get("animationNotices", []),
                interaction_notices=context.get("interactionNotices", []),
            )

    renderable = is_renderable_dsl(current)
    return _with_debug(
        current if renderable else FALLBACK_DSL,
        loop_count=repair_limit,
        before=errors_before,
        after=current_errors,
        used_fallback=not renderable,
        animation_notices=context.get("animationNotices", []),
        interaction_notices=context.get("interactionNotices", []),
    )


def stream_lockscreen_with_agent_loop(
    prompt: str,
    *,
    draft_stream_factory: Callable[[str], Any] | None = None,
    repairer: Callable[
        [str, dict[str, Any], list[dict[str, Any]], dict[str, Any]],
        dict[str, Any],
    ] = repair_dsl,
    max_repairs: int = MAX_REPAIR_ROUNDS,
):
    if draft_stream_factory is None:
        draft_stream_factory = generate_lockscreen_draft_stream
    try:
        draft = None
        context: dict[str, Any] = {}
        for event in draft_stream_factory(prompt):
            if event.get("type") == "draft_result":
                draft = event["dsl"]
                context = event.get("context") or {}
            else:
                yield event
        if draft is None:
            raise RuntimeError("Draft stream produced no DSL")
    except Exception as error:
        generation_error = [
            {
                "type": "generation_error",
                "level": "error",
                "message": str(error),
            }
        ]
        fallback = _with_debug(
            FALLBACK_DSL,
            loop_count=0,
            before=generation_error,
            after=generation_error,
            used_fallback=True,
            animation_notices=[],
            interaction_notices=[],
        )
        yield {
            "type": "error",
            "phase": "generation",
            "message": str(error),
        }
        yield {"type": "final", "dsl": fallback}
        return

    yield {
        "type": "phase",
        "phase": "validation",
        "status": "running",
        "label": "校验 DSL",
    }
    validation = _run_validators(draft, prompt, context)
    errors_before = copy.deepcopy(validation["errors"])
    yield {
        "type": "validation",
        "round": 0,
        "ok": validation["ok"],
        "errors": validation["errors"],
    }
    validation, animation_result = _run_animation_stage(
        validation,
        prompt,
        context,
    )
    if animation_result["applied"]:
        yield {
            "type": "animation_fallback",
            "phase": "animation",
            "status": "done",
            "animations": animation_result["applied"],
        }
    if animation_result["notices"]:
        yield {
            "type": "animation_unavailable",
            "phase": "animation",
            "status": "warning",
            "notices": animation_result["notices"],
        }
    if animation_result["applied"] or animation_result["notices"]:
        yield {
            "type": "validation",
            "round": 0,
            "ok": validation["ok"],
            "errors": validation["errors"],
        }
    validation, interaction_result = _run_interaction_stage(
        validation,
        prompt,
        context,
    )
    ready_interactions = interaction_result["applied"] or [
        {
            "target": str(interaction.get("targetId") or ""),
            "targetId": str(interaction.get("targetId") or ""),
            "trigger": str(
                (interaction.get("trigger") or {}).get("type") or ""
            ),
        }
        for interaction in validation["dsl"].get("interactions", [])
        if isinstance(interaction, dict)
    ]
    if ready_interactions:
        yield {
            "type": "interaction_ready",
            "phase": "interaction",
            "status": "done",
            "interactions": ready_interactions,
        }
    if interaction_result["notices"]:
        yield {
            "type": "interaction_unavailable",
            "phase": "interaction",
            "status": "warning",
            "notices": interaction_result["notices"],
        }
    if ready_interactions or interaction_result["notices"]:
        yield {
            "type": "validation",
            "round": 0,
            "ok": validation["ok"],
            "errors": validation["errors"],
        }
    fallback_dsl, fallback_layers = _inject_fallback_layers(
        validation["dsl"],
        validation["errors"],
        prompt,
        context,
    )
    if fallback_layers:
        yield {
            "type": "fallback_draw",
            "phase": "fallback",
            "status": "done",
            "targets": [layer["target"] for layer in fallback_layers],
            "layers": fallback_layers,
        }
        validation = _run_validators(fallback_dsl, prompt, context)
        yield {
            "type": "validation",
            "round": 0,
            "ok": validation["ok"],
            "errors": validation["errors"],
        }
    if validation["ok"]:
        final = _with_debug(
            validation["dsl"],
            loop_count=0,
            before=[],
            after=[],
            used_fallback=False,
            animation_notices=context.get("animationNotices", []),
            interaction_notices=context.get("interactionNotices", []),
        )
        yield {
            "type": "phase",
            "phase": "validation",
            "status": "done",
            "label": "校验通过",
        }
        yield {"type": "final", "dsl": final}
        return

    current = validation["dsl"]
    current_errors = validation["errors"]
    repair_limit = max(0, min(int(max_repairs), MAX_REPAIR_ROUNDS))
    for loop_count in range(1, repair_limit + 1):
        yield {
            "type": "repair",
            "round": loop_count,
            "status": "running",
            "label": f"执行第 {loop_count} 轮修复",
            "errors": current_errors,
        }
        try:
            current = repairer(prompt, current, current_errors, context)
        except Exception:
            pass
        validation = _run_validators(current, prompt, context)
        current = validation["dsl"]
        current_errors = validation["errors"]
        yield {
            "type": "validation",
            "round": loop_count,
            "ok": validation["ok"],
            "errors": current_errors,
        }
        if validation["ok"]:
            final = _with_debug(
                current,
                loop_count=loop_count,
                before=errors_before,
                after=[],
                used_fallback=False,
                animation_notices=context.get("animationNotices", []),
                interaction_notices=context.get("interactionNotices", []),
            )
            yield {
                "type": "repair",
                "round": loop_count,
                "status": "done",
                "label": "修复完成",
            }
            yield {"type": "final", "dsl": final}
            return

    renderable = is_renderable_dsl(current)
    fallback = _with_debug(
        current if renderable else FALLBACK_DSL,
        loop_count=repair_limit,
        before=errors_before,
        after=current_errors,
        used_fallback=not renderable,
        animation_notices=context.get("animationNotices", []),
        interaction_notices=context.get("interactionNotices", []),
    )
    if renderable:
        yield {
            "type": "phase",
            "phase": "validation",
            "status": "warning",
            "label": "部分问题未修复，已保留可用锁屏",
        }
        yield {"type": "final", "dsl": fallback}
        return
    yield {
        "type": "error",
        "phase": "repair",
        "message": "两轮修复后仍未通过校验，已使用 fallback DSL",
    }
    yield {"type": "final", "dsl": fallback}
