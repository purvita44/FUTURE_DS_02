import pandas as pd
import pytest

from analyze_campaigns import calculate_kpis, load_campaigns


def test_calculate_kpis():
    data = pd.DataFrame(
        {"campaign": ["A"], "spend": [100], "impressions": [1000], "clicks": [50], "conversions": [5], "revenue": [300]}
    )
    result = calculate_kpis(data)
    assert result.loc[0, "ctr_percent"] == 5
    assert result.loc[0, "roas"] == 3
    assert result.loc[0, "cpa"] == 20


def test_load_campaigns_requires_revenue(tmp_path):
    path = tmp_path / "campaigns.csv"
    pd.DataFrame({"campaign": ["A"], "spend": [1]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="revenue"):
        load_campaigns(path)
