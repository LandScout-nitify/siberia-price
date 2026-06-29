"""Пилотная обработка локальной таблицы земельных участков."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

import pandas as pd
import yaml

from siberia_price.normalization.vri import normalize_vri


REQUIRED_COLUMNS = (
    "region",
    "municipality",
    "settlement",
    "cadastral_number",
    "area_m2",
    "cadastral_value",
    "land_category",
    "permitted_use_raw",
    "address",
    "lat",
    "lon",
    "source",
    "notes",
)


def default_classifier_path() -> Path:
    """Вернуть путь к словарю ВРИ в рабочем дереве проекта."""
    return Path(__file__).resolve().parents[3] / "config" / "vri_classifier.yaml"


def load_classifier(path: str | Path | None = None) -> dict:
    """Загрузить YAML-конфигурацию классификатора ВРИ."""
    classifier_path = Path(path) if path is not None else default_classifier_path()
    with classifier_path.open(encoding="utf-8") as config_file:
        classifier = yaml.safe_load(config_file)

    if not isinstance(classifier, dict) or not classifier.get("groups"):
        raise ValueError(f"Некорректная конфигурация ВРИ: {classifier_path}")
    return classifier


def _to_classifiable_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    return str(value)


def _is_finite(value: object) -> bool:
    return pd.notna(value) and math.isfinite(float(value))


def _validation_reason(valid_area: bool, valid_value: bool) -> str | None:
    reasons = []
    if not valid_area:
        reasons.append("area_m2 must be a positive number")
    if not valid_value:
        reasons.append("cadastral_value must be a positive number")
    return "; ".join(reasons) or None


def process_land_dataframe(data: pd.DataFrame, classifier: dict) -> pd.DataFrame:
    """Провалидировать и классифицировать таблицу без потери исходных строк."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Отсутствуют обязательные столбцы: {missing}")

    result = data.copy()
    result["area_m2"] = pd.to_numeric(result["area_m2"], errors="coerce")
    result["cadastral_value"] = pd.to_numeric(
        result["cadastral_value"],
        errors="coerce",
    )

    valid_area = result["area_m2"].map(_is_finite) & result["area_m2"].gt(0)
    valid_value = (
        result["cadastral_value"].map(_is_finite)
        & result["cadastral_value"].gt(0)
    )
    valid_rows = valid_area & valid_value

    result["data_quality_status"] = valid_rows.map(
        {True: "valid", False: "invalid"},
    )
    result["data_quality_reason"] = [
        _validation_reason(area_is_valid, value_is_valid)
        for area_is_valid, value_is_valid in zip(
            valid_area,
            valid_value,
            strict=True,
        )
    ]
    result["cadastral_value_m2"] = (
        result["cadastral_value"] / result["area_m2"]
    ).where(valid_rows)

    matches = [
        normalize_vri(_to_classifiable_text(value), classifier)
        for value in result["permitted_use_raw"]
    ]
    result["permitted_use_norm"] = [match.group for match in matches]
    result["permitted_use_label"] = [match.label for match in matches]
    result["permitted_use_status"] = [match.status for match in matches]
    result["permitted_use_keyword"] = [
        match.matched_keyword for match in matches
    ]
    result["permitted_use_exclusion_reason"] = [
        match.exclusion_reason for match in matches
    ]

    return result


def process_land_table(
    input_path: str | Path,
    output_path: str | Path,
    classifier_path: str | Path | None = None,
) -> pd.DataFrame:
    """Прочитать CSV, обработать строки и сохранить результат в Parquet."""
    input_file = Path(input_path)
    output_file = Path(output_path)

    data = pd.read_csv(
        input_file,
        encoding="utf-8",
        dtype={"cadastral_number": "string"},
    )
    classifier = load_classifier(classifier_path)
    result = process_land_dataframe(data, classifier)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_file, index=False)
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Обработать локальную CSV-таблицу земельных участков.",
    )
    parser.add_argument("--input", required=True, help="Путь к входному CSV.")
    parser.add_argument(
        "--output",
        default="data/processed/industrial_land_sample_processed.parquet",
        help="Путь к выходному Parquet.",
    )
    parser.add_argument(
        "--classifier",
        default=None,
        help="Путь к YAML-классификатору ВРИ.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    result = process_land_table(
        input_path=args.input,
        output_path=args.output,
        classifier_path=args.classifier,
    )
    valid_count = int(result["data_quality_status"].eq("valid").sum())
    invalid_count = int(result["data_quality_status"].eq("invalid").sum())
    print(
        f"Обработано строк: {len(result)}; "
        f"валидных: {valid_count}; невалидных: {invalid_count}; "
        f"результат: {args.output}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
