from pathlib import Path

import pandas as pd
import pytest

from siberia_price.pipeline.process_land_table import (
    load_classifier,
    process_land_dataframe,
    process_land_table,
)


def _row(**overrides) -> dict:
    row = {
        "region": "Синтетический регион",
        "municipality": "Тестовый округ",
        "settlement": "Посёлок Пилотный",
        "cadastral_number": "SYNTH-TEST-001",
        "area_m2": 1000,
        "cadastral_value": 2_500_000,
        "land_category": "Земли населённых пунктов",
        "permitted_use_raw": "Промышленная площадка",
        "address": "Условный адрес",
        "lat": 55.0,
        "lon": 85.0,
        "source": "synthetic",
        "notes": "Тестовая синтетическая строка",
    }
    row.update(overrides)
    return row


@pytest.fixture(scope="module")
def classifier() -> dict:
    return load_classifier()


def test_pipeline_calculates_metric_and_classifies_rows(classifier):
    data = pd.DataFrame(
        [
            _row(cadastral_number="SYNTH-INCLUDED"),
            _row(
                cadastral_number="SYNTH-EXCLUDED",
                permitted_use_raw="Для индивидуального жилищного строительства",
            ),
            _row(
                cadastral_number="SYNTH-MANUAL",
                permitted_use_raw="Для иных видов использования",
            ),
            _row(
                cadastral_number="SYNTH-EMPTY",
                permitted_use_raw=None,
            ),
        ],
    )

    result = process_land_dataframe(data, classifier).set_index(
        "cadastral_number",
    )

    assert result.loc["SYNTH-INCLUDED", "cadastral_value_m2"] == 2500
    assert result.loc["SYNTH-INCLUDED", "permitted_use_status"] == "included"
    assert result.loc["SYNTH-INCLUDED", "permitted_use_norm"] == "industry"
    assert result.loc["SYNTH-EXCLUDED", "permitted_use_status"] == "excluded"
    assert result.loc["SYNTH-EXCLUDED", "permitted_use_exclusion_reason"]
    assert result.loc["SYNTH-MANUAL", "permitted_use_status"] == "manual_review"
    assert result.loc["SYNTH-EMPTY", "permitted_use_status"] == "manual_review"


@pytest.mark.parametrize(
    ("area_m2", "cadastral_value", "expected_reason"),
    [
        (0, 1_000_000, "area_m2"),
        (1000, 0, "cadastral_value"),
        ("not-a-number", 1_000_000, "area_m2"),
    ],
)
def test_invalid_numeric_rows_are_marked(
    classifier,
    area_m2,
    cadastral_value,
    expected_reason,
):
    data = pd.DataFrame(
        [_row(area_m2=area_m2, cadastral_value=cadastral_value)],
    )

    result = process_land_dataframe(data, classifier).iloc[0]

    assert result["data_quality_status"] == "invalid"
    assert expected_reason in result["data_quality_reason"]
    assert pd.isna(result["cadastral_value_m2"])


def test_pipeline_saves_parquet(tmp_path: Path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "nested" / "output.parquet"
    pd.DataFrame([_row()]).to_csv(input_path, index=False, encoding="utf-8")

    processed = process_land_table(input_path, output_path)
    restored = pd.read_parquet(output_path)

    assert output_path.is_file()
    assert len(processed) == len(restored) == 1
    assert restored.loc[0, "cadastral_value_m2"] == 2500
    assert restored.loc[0, "permitted_use_status"] == "included"


def test_example_contains_only_synthetic_cadastral_numbers():
    example_path = (
        Path(__file__).parents[1]
        / "data"
        / "examples"
        / "industrial_land_sample.csv"
    )
    sample = pd.read_csv(example_path, dtype={"cadastral_number": "string"})

    assert 10 <= len(sample) <= 15
    assert sample["cadastral_number"].str.startswith("SYNTH-").all()
    assert sample["source"].eq("synthetic").all()
