from pathlib import Path

import httpx
import pandas as pd
import pytest

from siberia_price.io.raw_store import load_raw_json, save_raw_json
from siberia_price.pipeline.process_nspd_raw_folder import (
    process_nspd_raw_folder,
)


EXAMPLES_DIR = Path(__file__).parents[1] / "data" / "examples" / "nspd"
PILOT_TEMPLATE = (
    Path(__file__).parents[1]
    / "data"
    / "examples"
    / "kyzyl_pilot_cadastral_numbers.csv"
)


def _copy_example(name: str, destination: Path) -> None:
    payload = load_raw_json(EXAMPLES_DIR / name)
    save_raw_json(payload, destination / name)


def test_raw_folder_pipeline_processes_and_saves_parquet(tmp_path: Path):
    input_dir = tmp_path / "raw"
    output_path = tmp_path / "processed" / "pilot.parquet"
    _copy_example("industrial_feature.json", input_dir)
    _copy_example("warehouse_feature.json", input_dir)
    _copy_example("incomplete_feature.json", input_dir)

    result = process_nspd_raw_folder(input_dir, output_path)
    restored = pd.read_parquet(output_path).set_index("cadastral_number")
    indexed = result.set_index("cadastral_number")

    assert output_path.is_file()
    assert len(result) == len(restored) == 3
    assert indexed.loc["SYNTH-NSPD-001", "cadastral_value_m2"] == 1500
    assert indexed.loc["SYNTH-NSPD-001", "permitted_use_norm"] == "industry"
    assert indexed.loc["SYNTH-NSPD-001", "permitted_use_status"] == "included"
    assert indexed.loc["SYNTH-NSPD-002", "permitted_use_norm"] == "warehouse"
    assert indexed.loc["SYNTH-NSPD-003", "permitted_use_status"] == (
        "manual_review"
    )
    assert indexed.loc["SYNTH-NSPD-003", "data_quality_status"] == "invalid"
    assert pd.isna(indexed.loc["SYNTH-NSPD-003", "cadastral_value_m2"])
    assert restored.loc["SYNTH-NSPD-001", "raw_file"] == (
        "industrial_feature.json"
    )


def test_raw_folder_pipeline_does_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    input_dir = tmp_path / "raw"
    _copy_example("industrial_feature.json", input_dir)

    def fail_on_network(*args, **kwargs):
        raise AssertionError("Сетевые запросы запрещены в raw-пайплайне")

    monkeypatch.setattr(httpx, "Client", fail_on_network)

    result = process_nspd_raw_folder(
        input_dir,
        tmp_path / "processed.parquet",
    )

    assert len(result) == 1
    assert result.loc[0, "source"] == "nspd"


def test_raw_folder_pipeline_rejects_empty_folder(tmp_path: Path):
    input_dir = tmp_path / "empty"
    input_dir.mkdir()

    with pytest.raises(ValueError, match="нет JSON-файлов"):
        process_nspd_raw_folder(input_dir, tmp_path / "output.parquet")


def test_pilot_template_contains_only_placeholders():
    pilot_list = pd.read_csv(
        PILOT_TEMPLATE,
        dtype={"cadastral_number": "string"},
    )
    cadastral_numbers = pilot_list["cadastral_number"]

    assert cadastral_numbers.str.contains("X", regex=False).all()
    assert not cadastral_numbers.str.fullmatch(
        r"\d{2}:\d{2}:\d+:\d+",
    ).any()
