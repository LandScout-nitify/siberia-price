"""Безопасное локальное хранение исходных JSON-ответов."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_raw_json(payload: Any, output_path: str | Path) -> Path:
    """Атомарно сохранить JSON в UTF-8 и вернуть итоговый путь."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            file.write("\n")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return path


def load_raw_json(input_path: str | Path) -> Any:
    """Загрузить сохранённый JSON без преобразования его структуры."""
    path = Path(input_path)
    with path.open(encoding="utf-8") as file:
        return json.load(file)
