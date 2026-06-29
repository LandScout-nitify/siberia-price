"""Парсинг локально сохранённых ответов НСПД в единую структуру."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "cadastral_number": ("cad_num", "cn", "cadastral_number"),
    "area_m2": ("declared_area", "area", "area_m2"),
    "cadastral_value": ("cost_value", "cadastral_value"),
    "land_category": (
        "land_category",
        "category",
        "readable_category",
    ),
    "permitted_use_raw": (
        "permitted_use",
        "readable_vri",
        "permitted_use_established_by_document",
    ),
    "address": ("readable_address", "address"),
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_value(
    sources: Sequence[Mapping[str, Any]],
    aliases: Sequence[str],
) -> Any | None:
    """Найти первое непустое значение по явно заданному списку имён."""
    for source in sources:
        for alias in aliases:
            if alias in source and source[alias] not in (None, ""):
                return source[alias]
    return None


def _optional_number(value: Any | None) -> int | float | None:
    """Преобразовать числовую строку, сохранив целые значения целыми."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        normalized = value.strip().replace(" ", "").replace(",", ".")
        if not normalized:
            return None
        try:
            number = float(normalized)
        except (ValueError, OverflowError):
            return None
        if not math.isfinite(number):
            return None
        return int(number) if number.is_integer() else number
    return None


def parse_nspd_feature(feature: Mapping[str, Any]) -> dict[str, Any]:
    """Преобразовать GeoJSON-подобный объект НСПД в плоскую запись.

    Поддерживаются только перечисленные в ``FIELD_ALIASES`` варианты имён.
    Функция не выполняет сетевых запросов и возвращает ``None`` для
    отсутствующих или некорректных полей.
    """
    root = _mapping(feature)
    properties = _mapping(root.get("properties"))
    sources = (properties, root)

    parsed = {
        output_field: _first_value(sources, aliases)
        for output_field, aliases in FIELD_ALIASES.items()
    }
    parsed["area_m2"] = _optional_number(parsed["area_m2"])
    parsed["cadastral_value"] = _optional_number(parsed["cadastral_value"])
    parsed["geometry"] = root.get("geometry")
    parsed["source"] = "nspd"
    return parsed
