"""Обработка небольшой локальной папки с raw JSON-карточками НСПД."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from siberia_price.io.raw_store import load_raw_json
from siberia_price.nspd.parser import parse_nspd_feature
from siberia_price.pipeline.process_land_table import (
    REQUIRED_COLUMNS,
    load_classifier,
    process_land_dataframe,
)


def _record_from_raw_file(path: Path) -> dict[str, Any]:
    payload = load_raw_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Ожидался JSON-объект в файле: {path}")

    record = parse_nspd_feature(payload)
    geometry = record.get("geometry")
    if geometry is not None:
        record["geometry"] = json.dumps(
            geometry,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )

    record["raw_file"] = path.name
    for column in REQUIRED_COLUMNS:
        record.setdefault(column, None)
    return record


def process_nspd_raw_folder(
    input_dir: str | Path,
    output_path: str | Path,
    classifier_path: str | Path | None = None,
) -> pd.DataFrame:
    """Собрать raw JSON из одной папки и сохранить processed Parquet."""
    input_directory = Path(input_dir)
    output_file = Path(output_path)

    if not input_directory.is_dir():
        raise FileNotFoundError(f"Папка raw JSON не найдена: {input_directory}")

    json_files = sorted(input_directory.glob("*.json"))
    if not json_files:
        raise ValueError(f"В папке нет JSON-файлов: {input_directory}")

    records = [_record_from_raw_file(path) for path in json_files]
    data = pd.DataFrame(records)
    classifier = load_classifier(classifier_path)
    result = process_land_dataframe(data, classifier)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_file, index=False)
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Обработать локальную папку raw JSON НСПД без сети.",
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Папка с вручную сохранёнными JSON-карточками.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/kyzyl_pilot_processed.parquet",
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
    result = process_nspd_raw_folder(
        input_dir=args.input_dir,
        output_path=args.output,
        classifier_path=args.classifier,
    )
    print(
        f"Обработано raw JSON: {len(result)}; результат: {args.output}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
