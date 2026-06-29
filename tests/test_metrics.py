import pandas as pd

from siberia_price.analytics.metrics import add_cadastral_value_m2, weighted_cadastral_value_m2


def test_add_cadastral_value_m2():
    df = pd.DataFrame({"cadastral_value": [1000, 3000], "area_m2": [10, 30]})
    result = add_cadastral_value_m2(df)
    assert result["cadastral_value_m2"].tolist() == [100, 100]


def test_weighted_cadastral_value_m2():
    df = pd.DataFrame({"cadastral_value": [1000, 3000], "area_m2": [10, 30]})
    assert weighted_cadastral_value_m2(df) == 100
