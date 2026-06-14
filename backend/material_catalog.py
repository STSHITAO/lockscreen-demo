import copy
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


MATERIALS_PATH = Path(__file__).parent.parent / "public" / "materials"
CATALOG_PATHS = (
    MATERIALS_PATH / "assets.json",
    MATERIALS_PATH / "animations.json",
)
SEARCH_FIELDS = (
    "subjects",
    "keywords",
    "themes",
    "moods",
    "roles",
    "colors",
    "style",
)
FIELD_WEIGHTS = {
    "subjects": 40,
    "roles": 18,
    "themes": 14,
    "moods": 9,
    "colors": 5,
    "keywords": 12,
    "style": 3,
}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def _values(asset: dict[str, Any], field: str) -> set[str]:
    return {_normalized(value) for value in _list(asset.get(field)) if _normalized(value)}


def _requested(requirement: dict[str, Any], field: str) -> set[str]:
    return {
        _normalized(value)
        for value in _list(requirement.get(field))
        if _normalized(value)
    }


@lru_cache(maxsize=1)
def _catalog() -> tuple[dict[str, Any], ...]:
    materials = []
    for catalog_path in CATALOG_PATHS:
        with catalog_path.open("r", encoding="utf-8") as catalog_file:
            catalog = json.load(catalog_file)
        if not isinstance(catalog, list):
            raise ValueError(
                f"Material catalog must contain a JSON array: {catalog_path.name}"
            )
        materials.extend(
            material for material in catalog if isinstance(material, dict)
        )
    return tuple(materials)


@lru_cache(maxsize=1)
def _catalog_by_id() -> dict[str, dict[str, Any]]:
    return {
        str(material.get("assetId")): material
        for material in _catalog()
        if material.get("assetId")
    }


def load_materials() -> list[dict[str, Any]]:
    return copy.deepcopy(list(_catalog()))


def get_asset(asset_id: str) -> dict[str, Any] | None:
    material = _catalog_by_id().get(str(asset_id or ""))
    return copy.deepcopy(material) if material else None


def _query_tokens(query: str) -> list[str]:
    normalized = _normalized(query)
    latin_tokens = re.findall(r"[a-z0-9-]+", normalized)
    return list(dict.fromkeys([normalized, *latin_tokens])) if normalized else []


def _searchable_terms(asset: dict[str, Any]) -> list[str]:
    name = asset.get("name") if isinstance(asset.get("name"), dict) else {}
    values = [
        asset.get("assetId"),
        name.get("zh"),
        name.get("en"),
        asset.get("description"),
        asset.get("category"),
    ]
    for field in SEARCH_FIELDS:
        values.extend(_list(asset.get(field)))
    return [_normalized(value) for value in values if _normalized(value)]


def _score(asset: dict[str, Any], requirement: dict[str, Any]) -> int:
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        overlap = _values(asset, field) & _requested(requirement, field)
        score += len(overlap) * weight

    requested_categories = _requested(requirement, "categories")
    if _normalized(asset.get("category")) in requested_categories:
        score += 22

    query = _normalized(requirement.get("query"))
    terms = _searchable_terms(asset)
    haystack = " ".join(terms)
    for token in _query_tokens(query):
        if token and token in haystack:
            score += 10
    for term in terms:
        if query and len(term) >= 2 and term in query:
            score += 8
    name = asset.get("name") if isinstance(asset.get("name"), dict) else {}
    for language in ("zh", "en"):
        material_name = _normalized(name.get(language))
        if query and material_name and (
            material_name in query or query in material_name
        ):
            score += 20
    return score


def search_materials(
    requirement: dict[str, Any] | None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    requirement = requirement if isinstance(requirement, dict) else {}
    requested_subjects = _requested(requirement, "subjects")
    requested_categories = _requested(requirement, "categories")
    ranked: list[tuple[int, dict[str, Any]]] = []

    for material in _catalog():
        if requested_subjects and not (requested_subjects & _values(material, "subjects")):
            continue
        if requested_categories and _normalized(material.get("category")) not in requested_categories:
            continue
        score = _score(material, requirement)
        if score > 0 or not any(
            (
                _normalized(requirement.get("query")),
                requested_subjects,
                _requested(requirement, "roles"),
                requested_categories,
                _requested(requirement, "themes"),
                _requested(requirement, "moods"),
                _requested(requirement, "colors"),
            )
        ):
            ranked.append((score, material))

    ranked.sort(key=lambda item: (-item[0], str(item[1].get("assetId") or "")))
    safe_limit = max(1, min(int(limit or 5), 20))
    return [copy.deepcopy(material) for _, material in ranked[:safe_limit]]


def compact_material(material: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(material.get(key))
        for key in (
            "assetId",
            "assetType",
            "name",
            "description",
            "category",
            "subjects",
            "themes",
            "moods",
            "roles",
            "colors",
            "recommendedPositions",
            "visualWeight",
            "viewBox",
            "frameCount",
            "fps",
            "loop",
        )
    }
