"""Нормализация видов разрешенного использования."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VriMatch:
    group: str | None
    label: str | None
    matched_keyword: str | None


def normalize_vri(raw_text: str | None, classifier: dict) -> VriMatch:
    """Простая нормализация ВРИ по словарю ключевых слов.

    На первом этапе используем объяснимую словарную логику.
    Fuzzy matching можно добавить позже.
    """
    if not raw_text:
        return VriMatch(None, None, None)

    text = raw_text.lower()

    for group_name, group_data in classifier.get("groups", {}).items():
        exclude_keywords = group_data.get("exclude_keywords") or []
        if any(keyword.lower() in text for keyword in exclude_keywords):
            continue

        include_keywords = group_data.get("include_keywords") or []
        for keyword in include_keywords:
            if keyword.lower() in text:
                return VriMatch(
                    group=group_name,
                    label=group_data.get("label"),
                    matched_keyword=keyword,
                )

    return VriMatch(None, None, None)
