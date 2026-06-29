"""Обработка выбросов."""

from __future__ import annotations

import pandas as pd


def iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    """Границы выбросов по IQR."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def mark_outliers_iqr(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Добавляет флаг выброса."""
    result = df.copy()
    low, high = iqr_bounds(result[col].dropna())
    result[f"{col}_is_outlier"] = (result[col] < low) | (result[col] > high)
    return result
