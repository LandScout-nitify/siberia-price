"""Парсинг ответов НСПД в единую структуру."""

from __future__ import annotations

from typing import Any


def parse_nspd_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Преобразует объект НСПД в плоскую запись.

    TODO: уточнить поля после получения реальных ответов НСПД.
    """
    properties = feature.get("properties", {})
    geometry = feature.get("geometry")

    return {
        "cadastral_number": properties.get("cad_num") or properties.get("cn"),
        "area_m2": properties.get("declared_area"),
        "cadastral_value": properties.get("cost_value"),
        "permitted_use_raw": properties.get("permitted_use") or properties.get("readable_vri"),
        "address": properties.get("readable_address"),
        "geometry": geometry,
        "source": "nspd",
    }
