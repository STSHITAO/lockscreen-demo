import re
from typing import Any

from .shape_defaults import (
    TARGET_ALIASES,
    normalize_position_hint,
    normalize_target,
)


SUPPORTED_ANIMATIONS = {
    "float",
    "pulse",
    "rotate",
    "twinkle",
    "drift-left",
    "drift-right",
    "sway",
    "bounce",
    "fade",
    "breathe",
}

MOTION_ALIASES = {
    "drift-left": (
        "drift-left",
        "drift left",
        "\u5411\u5de6\u98d8",
        "\u5411\u5de6\u6f02",
    ),
    "drift-right": (
        "drift-right",
        "drift right",
        "\u5411\u53f3\u98d8",
        "\u5411\u53f3\u6f02",
        "\u98d8\u52a8",
        "\u98d8\u8fc7",
    ),
    "twinkle": (
        "twinkle",
        "twinkling",
        "blink",
        "\u95ea\u70c1",
        "\u7728\u773c",
        "\u5ffd\u660e\u5ffd\u6697",
    ),
    "pulse": (
        "pulse",
        "heartbeat",
        "heart beat",
        "beating",
        "\u8df3\u52a8",
        "\u5fc3\u8df3",
        "\u640f\u52a8",
    ),
    "rotate": (
        "rotate",
        "rotating",
        "spin",
        "spinning",
        "\u65cb\u8f6c",
        "\u8f6c\u52a8",
    ),
    "sway": ("sway", "swing", "\u6447\u6446", "\u6446\u52a8"),
    "bounce": ("bounce", "bouncing", "\u5f39\u8df3", "\u8e66\u8df3"),
    "fade": ("fade", "fade in", "fade out", "\u6e10\u9690", "\u6de1\u5165\u6de1\u51fa"),
    "breathe": ("breathe", "breathing", "\u547c\u5438", "\u547c\u5438\u611f"),
    "float": ("float", "floating", "\u6f02\u6d6e", "\u6d6e\u52a8"),
}

COMPLEX_MOTION_KEYWORDS = (
    "transform",
    "morph",
    "walk",
    "dance",
    "fly away",
    "explosion",
    "cinematic",
    "\u53d8\u5f62",
    "\u53d8\u6210",
    "\u884c\u8d70",
    "\u8df3\u821e",
    "\u98de\u8d70",
    "\u7206\u70b8",
    "\u8fd0\u955c",
)


def normalize_motion(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("_", "-")
    if text in SUPPORTED_ANIMATIONS:
        return text
    for motion, aliases in MOTION_ALIASES.items():
        if any(alias in text for alias in aliases):
            return motion
    return None


def _target_in_clause(clause: str) -> str | None:
    for target, aliases in TARGET_ALIASES.items():
        if any(alias.lower() in clause for alias in aliases):
            return target
    return None


def extract_animation_requirements(prompt: str) -> list[dict[str, str]]:
    text = str(prompt or "").lower()
    clauses = [
        clause.strip()
        for clause in re.split(r"[,.;:!?\n\u3002\uff0c\uff1b\uff1a\uff01\uff1f]+", text)
        if clause.strip()
    ]
    requirements = []
    seen_targets = set()
    for clause in clauses:
        target = _target_in_clause(clause)
        if not target or target in seen_targets:
            continue
        motion = normalize_motion(clause)
        complex_motion = any(keyword in clause for keyword in COMPLEX_MOTION_KEYWORDS)
        if not motion and not complex_motion:
            continue
        requirements.append(
            {
                "target": target,
                "motion": motion or "complex-motion",
                "complexity": "complex" if complex_motion and not motion else "simple",
                "preferredPosition": "center",
            }
        )
        seen_targets.add(target)
        if len(requirements) >= 3:
            break
    return requirements


def normalize_animation_requirements(
    value: Any,
    prompt: str,
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return extract_animation_requirements(prompt)

    requirements = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        raw_target = str(raw.get("target") or "").strip().lower()
        if not raw_target:
            continue
        target = normalize_target(raw_target) or raw_target[:80]
        requested_complexity = str(raw.get("complexity") or "simple").lower()
        motion_value = str(raw.get("motion") or "").strip()
        motion = normalize_motion(motion_value)
        complexity = (
            "complex"
            if requested_complexity == "complex" or motion is None
            else "simple"
        )
        requirements.append(
            {
                "target": target,
                "motion": motion or motion_value[:80] or "complex-motion",
                "complexity": complexity,
                "preferredPosition": normalize_position_hint(
                    raw.get("preferredPosition")
                ),
            }
        )
        if len(requirements) >= 3:
            break
    prompt_requirements = extract_animation_requirements(prompt)
    by_target = {
        requirement["target"]: index
        for index, requirement in enumerate(requirements)
    }
    for prompt_requirement in prompt_requirements:
        target = prompt_requirement["target"]
        if target in by_target:
            existing = requirements[by_target[target]]
            requirements[by_target[target]] = {
                **existing,
                **prompt_requirement,
                "preferredPosition": (
                    existing.get("preferredPosition")
                    or prompt_requirement.get("preferredPosition")
                    or "center"
                ),
            }
        elif len(requirements) < 3:
            by_target[target] = len(requirements)
            requirements.append(prompt_requirement)
    return requirements or prompt_requirements
