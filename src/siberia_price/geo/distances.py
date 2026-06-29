"""Географические расстояния и локационные факторы."""

from __future__ import annotations

import geopandas as gpd


def add_centroids(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Добавляет центроид геометрии участка."""
    result = gdf.copy()
    projected = result.to_crs(result.estimate_utm_crs())
    result["centroid"] = projected.geometry.centroid.to_crs(result.crs)
    return result
