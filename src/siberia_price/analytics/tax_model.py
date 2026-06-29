"""Модель налоговой нагрузки."""

from __future__ import annotations


def land_tax(cadastral_value: float, tax_rate: float = 0.015) -> float:
    """Расчет земельного налога."""
    return cadastral_value * tax_rate


def tax_for_area(area_m2: float, cadastral_value_m2: float, tax_rate: float = 0.015) -> float:
    """Налог для типового участка по площади и КС 1 м²."""
    return land_tax(area_m2 * cadastral_value_m2, tax_rate)
