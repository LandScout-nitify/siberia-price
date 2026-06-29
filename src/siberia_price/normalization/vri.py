"""Объяснимая нормализация видов разрешённого использования."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


ClassificationStatus = Literal["included", "excluded", "manual_review"]


@dataclass(frozen=True)
class VriMatch:
    """Результат классификации с данными, объясняющими решение."""

    status: ClassificationStatus
    group: str | None
    label: str | None
    matched_keyword: str | None
    exclusion_reason: str | None


def _normalize_text(value: str) -> str:
    """Привести текст к форме для регистронезависимого поиска фраз."""
    return re.sub(r"\s+", " ", value.casefold().replace("ё", "е")).strip()


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    """Вернуть совпавшие ключи от наиболее специфичного к короткому."""
    matches = {
        keyword
        for keyword in keywords
        if keyword and _normalize_text(keyword) in text
    }
    return sorted(matches, key=lambda keyword: (-len(_normalize_text(keyword)), keyword))


def _manual_review(
    classifier: dict,
    matched_keyword: str | None = None,
) -> VriMatch:
    manual_config = classifier.get("manual_review", {})
    return VriMatch(
        status="manual_review",
        group=None,
        label=manual_config.get("label", "Требуется ручная проверка"),
        matched_keyword=matched_keyword,
        exclusion_reason=None,
    )


def normalize_vri(raw_text: str | None, classifier: dict) -> VriMatch:
    """Классифицировать ВРИ по явным правилам из конфигурации.

    Приоритет правил:
    1. исключающий признак;
    2. явный признак ручной проверки;
    3. единственная совпавшая нормализованная группа;
    4. ручная проверка при нескольких группах или отсутствии совпадений.
    """
    if not raw_text or not raw_text.strip():
        return _manual_review(classifier)

    text = _normalize_text(raw_text)

    exclusion_matches: list[tuple[str, dict, str]] = []
    for exclusion_name, exclusion_data in classifier.get("exclusions", {}).items():
        matches = _find_keywords(text, exclusion_data.get("keywords") or [])
        if matches:
            exclusion_matches.append((exclusion_name, exclusion_data, matches[0]))

    if exclusion_matches:
        _, exclusion_data, keyword = min(
            exclusion_matches,
            key=lambda match: (-len(_normalize_text(match[2])), match[0]),
        )
        return VriMatch(
            status="excluded",
            group=None,
            label=exclusion_data.get("label"),
            matched_keyword=keyword,
            exclusion_reason=exclusion_data.get("reason"),
        )

    manual_config = classifier.get("manual_review", {})
    manual_matches = _find_keywords(text, manual_config.get("keywords") or [])
    if manual_matches:
        return _manual_review(classifier, manual_matches[0])

    group_matches: list[tuple[str, dict, str]] = []
    for group_name, group_data in classifier.get("groups", {}).items():
        matches = _find_keywords(text, group_data.get("include_keywords") or [])
        if matches:
            group_matches.append((group_name, group_data, matches[0]))

    if len(group_matches) != 1:
        keyword = None
        if group_matches:
            keyword = min(
                group_matches,
                key=lambda match: (-len(_normalize_text(match[2])), match[0]),
            )[2]
        return _manual_review(classifier, keyword)

    group_name, group_data, keyword = group_matches[0]
    return VriMatch(
        status="included",
        group=group_name,
        label=group_data.get("label"),
        matched_keyword=keyword,
        exclusion_reason=None,
    )
