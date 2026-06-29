from pathlib import Path

import httpx
import pytest

from siberia_price.io.raw_store import load_raw_json, save_raw_json
from siberia_price.nspd.parser import parse_nspd_feature


EXAMPLES_DIR = Path(__file__).parents[1] / "data" / "examples" / "nspd"


def test_parser_reads_complete_industrial_json():
    payload = load_raw_json(EXAMPLES_DIR / "industrial_feature.json")

    result = parse_nspd_feature(payload)

    assert result == {
        "cadastral_number": "SYNTH-NSPD-001",
        "area_m2": 12500.0,
        "cadastral_value": 18750000.0,
        "land_category": "Земли населённых пунктов",
        "permitted_use_raw": "Промышленное производство — кирпичный завод",
        "address": (
            "Синтетический регион, условная промышленная площадка 1"
        ),
        "geometry": payload["geometry"],
        "source": "nspd",
    }


def test_parser_supports_alternative_field_names():
    payload = load_raw_json(EXAMPLES_DIR / "warehouse_feature.json")

    result = parse_nspd_feature(payload)

    assert result["cadastral_number"] == "SYNTH-NSPD-002"
    assert result["area_m2"] == 6400
    assert result["cadastral_value"] == 7680000
    assert result["land_category"] == "Земли населённых пунктов"
    assert result["permitted_use_raw"] == (
        "Складской комплекс и складское хранение"
    )
    assert result["address"] == (
        "Синтетический регион, условный складской проезд 2"
    )
    assert result["geometry"] == payload["geometry"]
    assert result["source"] == "nspd"


def test_parser_returns_none_for_missing_fields():
    payload = load_raw_json(EXAMPLES_DIR / "incomplete_feature.json")

    result = parse_nspd_feature(payload)

    assert result["cadastral_number"] == "SYNTH-NSPD-003"
    assert result["area_m2"] is None
    assert result["cadastral_value"] is None
    assert result["land_category"] == "Земли населённых пунктов"
    assert result["permitted_use_raw"] is None
    assert result["address"] is None
    assert result["geometry"] is None
    assert result["source"] == "nspd"


def test_parser_reads_flat_remaining_aliases():
    payload = {
        "cadastral_number": "SYNTH-NSPD-FLAT",
        "area_m2": "2500,5",
        "cost_value": "not-a-number",
        "permitted_use_established_by_document": (
            "Производственная площадка"
        ),
        "address": "Синтетический адрес",
    }

    result = parse_nspd_feature(payload)

    assert result["cadastral_number"] == "SYNTH-NSPD-FLAT"
    assert result["area_m2"] == 2500.5
    assert result["cadastral_value"] is None
    assert result["permitted_use_raw"] == "Производственная площадка"
    assert result["address"] == "Синтетический адрес"


def test_parser_handles_missing_properties():
    result = parse_nspd_feature({})

    assert result == {
        "cadastral_number": None,
        "area_m2": None,
        "cadastral_value": None,
        "land_category": None,
        "permitted_use_raw": None,
        "address": None,
        "geometry": None,
        "source": "nspd",
    }


def test_raw_json_round_trip_is_lossless(tmp_path: Path):
    payload = {
        "id": "SYNTH-NSPD-ROUNDTRIP",
        "unicode": "Промышленная площадка",
        "nested": {
            "values": [1, 2.5, True, None],
            "geometry": {"type": "Point", "coordinates": [85.1, 55.2]},
        },
    }
    output_path = tmp_path / "raw" / "response.json"

    saved_path = save_raw_json(payload, output_path)
    restored = load_raw_json(saved_path)

    assert saved_path == output_path
    assert restored == payload


def test_local_parser_and_store_do_not_access_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    def fail_on_network(*args, **kwargs):
        raise AssertionError("Сетевой клиент не должен вызываться")

    monkeypatch.setattr(httpx, "Client", fail_on_network)
    payload = load_raw_json(EXAMPLES_DIR / "industrial_feature.json")
    result = parse_nspd_feature(payload)
    saved_path = save_raw_json(payload, tmp_path / "copy.json")

    assert result["cadastral_number"] == "SYNTH-NSPD-001"
    assert load_raw_json(saved_path) == payload
