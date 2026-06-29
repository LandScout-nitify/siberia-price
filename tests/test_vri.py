from pathlib import Path

import pytest
import yaml

from siberia_price.normalization.vri import normalize_vri


@pytest.fixture(scope="module")
def classifier() -> dict:
    config_path = Path(__file__).parents[1] / "config" / "vri_classifier.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


@pytest.mark.parametrize(
    ("raw_text", "expected_group"),
    [
        ("Для размещения объектов промышленного производства", "industry"),
        ("Производственная площадка кирпичного завода", "industry"),
        ("Складской комплекс и складское хранение", "warehouse"),
        ("Коммунально-производственная зона", "utility_industrial"),
        ("Для размещения трансформаторной подстанции", "energy"),
        ("Транспортно-логистический центр", "transport_logistics"),
    ],
)
def test_included_vri_groups(classifier, raw_text, expected_group):
    result = normalize_vri(raw_text, classifier)

    assert result.status == "included"
    assert result.group == expected_group
    assert result.label
    assert result.matched_keyword
    assert result.exclusion_reason is None


@pytest.mark.parametrize(
    "raw_text",
    [
        "Для индивидуального жилищного строительства (ИЖС)",
        "Для ведения личного подсобного хозяйства (ЛПХ)",
        "Для ведения садоводства, СНТ",
        "Для сельскохозяйственного производства",
        "Полоса отвода железной дороги",
        "Для размещения линейного объекта — газопровода",
    ],
)
def test_non_industrial_vri_is_excluded(classifier, raw_text):
    result = normalize_vri(raw_text, classifier)

    assert result.status == "excluded"
    assert result.group is None
    assert result.label
    assert result.matched_keyword
    assert result.exclusion_reason


@pytest.mark.parametrize(
    "raw_text",
    [
        "Для иных видов использования",
        "Производственная деятельность и складское хранение",
        "Объекты делового управления",
        None,
    ],
)
def test_ambiguous_or_unknown_vri_requires_manual_review(classifier, raw_text):
    result = normalize_vri(raw_text, classifier)

    assert result.status == "manual_review"
    assert result.group is None
    assert result.label == "Требуется ручная проверка"
    assert result.exclusion_reason is None


def test_exclusion_has_priority_over_inclusion(classifier):
    result = normalize_vri(
        "Складская площадка в полосе отвода автомобильной дороги",
        classifier,
    )

    assert result.status == "excluded"
    assert result.group is None
    assert result.matched_keyword == "полосе отвода автомобильной дороги"
