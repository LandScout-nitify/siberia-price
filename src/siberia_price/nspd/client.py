"""Клиент НСПД.

Важно: этот модуль пока является каркасом.
Перед массовым сбором нужно зафиксировать актуальные endpoint'ы НСПД,
лимиты, формат ответа и правила сохранения сырых данных.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class NspdClient:
    base_url: str
    timeout: float = 30.0

    def get_by_cadastral_number(self, cadastral_number: str) -> dict[str, Any]:
        """Получить сведения по кадастровому номеру.

        TODO: реализовать после фиксации актуального endpoint НСПД.
        """
        raise NotImplementedError("Нужно реализовать актуальный запрос к НСПД.")

    def request_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Вспомогательный метод GET-запроса."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
