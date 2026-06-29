"""Расчет базовых кадастровых метрик."""

from __future__ import annotations

import pandas as pd


def add_cadastral_value_m2(
    df: pd.DataFrame,
    value_col: str = "cadastral_value",
    area_col: str = "area_m2",
    output_col: str = "cadastral_value_m2",
) -> pd.DataFrame:
    """Добавляет удельную кадастровую стоимость 1 м²."""
    result = df.copy()
    result[output_col] = result[value_col] / result[area_col]
    return result


def weighted_cadastral_value_m2(
    df: pd.DataFrame,
    value_col: str = "cadastral_value",
    area_col: str = "area_m2",
) -> float:
    """Средневзвешенная кадастровая стоимость 1 м²."""
    total_area = df[area_col].sum()
    if total_area == 0:
        return float("nan")
    return df[value_col].sum() / total_area


def regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Сводка по регионам."""
    rows = []
    for region, part in df.groupby("region"):
        rows.append(
            {
                "region": region,
                "plots_count": len(part),
                "total_area_m2": part["area_m2"].sum(),
                "mean_cv_m2": part["cadastral_value_m2"].mean(),
                "median_cv_m2": part["cadastral_value_m2"].median(),
                "weighted_cv_m2": weighted_cadastral_value_m2(part),
                "p25_cv_m2": part["cadastral_value_m2"].quantile(0.25),
                "p75_cv_m2": part["cadastral_value_m2"].quantile(0.75),
            }
        )
    return pd.DataFrame(rows)
