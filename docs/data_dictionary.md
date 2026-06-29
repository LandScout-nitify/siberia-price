# Словарь данных

| Поле | Тип | Описание |
|---|---|---|
| region | string | субъект РФ |
| municipality | string | муниципалитет |
| settlement | string | населенный пункт |
| cadastral_number | string | кадастровый номер |
| area_m2 | float | площадь участка |
| cadastral_value | float | кадастровая стоимость |
| cadastral_value_m2 | float | кадастровая стоимость 1 м² |
| land_category | string | категория земель |
| permitted_use_raw | string | исходный ВРИ |
| permitted_use_norm | string | нормализованный ВРИ |
| location_type | string | тип локации |
| lat | float | широта |
| lon | float | долгота |
| geometry | geometry | геометрия участка |
| distance_city_center_km | float | расстояние до центра города |
| distance_road_km | float | расстояние до автодороги |
| distance_rail_km | float | расстояние до железной дороги |
| distance_airport_km | float | расстояние до аэропорта |
| pzz_zone | string | территориальная зона |
| valuation_date | date | дата оценки |
| source | string | источник данных |
| market_price_m2 | float | рыночная цена 1 м² |
| market_source | string | источник рыночной цены |
| cadastral_to_market_ratio | float | КС / рынок |
| notes | string | комментарии |
