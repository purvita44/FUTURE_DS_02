"""Calculate social media campaign KPIs and generate an insight report."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

REQUIRED_COLUMNS = {"campaign", "spend", "impressions", "clicks", "conversions", "revenue"}


def load_campaigns(path: str | Path) -> pd.DataFrame:
    """Load campaign data and validate its required metrics."""
    data = pd.read_csv(path)
    data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_")
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    for column in REQUIRED_COLUMNS - {"campaign"}:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=REQUIRED_COLUMNS).copy()
    if (data[["spend", "impressions", "clicks", "conversions", "revenue"]] < 0).any().any():
        raise ValueError("Metrics cannot be negative.")
    return data.reset_index(drop=True)


def calculate_kpis(data: pd.DataFrame) -> pd.DataFrame:
    """Add CTR, CPC, conversion rate, CPA, and ROAS columns."""
    result = data.copy()
    result["ctr_percent"] = (result["clicks"] / result["impressions"].replace(0, pd.NA) * 100).fillna(0)
    result["cpc"] = (result["spend"] / result["clicks"].replace(0, pd.NA)).fillna(0)
    result["conversion_rate_percent"] = (result["conversions"] / result["clicks"].replace(0, pd.NA) * 100).fillna(0)
    result["cpa"] = (result["spend"] / result["conversions"].replace(0, pd.NA)).fillna(0)
    result["roas"] = (result["revenue"] / result["spend"].replace(0, pd.NA)).fillna(0)
    return result


def write_outputs(data: pd.DataFrame, output_dir: str | Path) -> pd.DataFrame:
    """Create KPI data, visualizations, and concise recommendations."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    kpis = calculate_kpis(data)
    kpis.round(2).to_csv(output / "campaign_kpis.csv", index=False)

    sns.set_theme(style="whitegrid")
    ranked = kpis.sort_values("roas", ascending=False)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=ranked, x="roas", y="campaign", color="#59A14F")
    plt.xlabel("Return on ad spend (ROAS)")
    plt.ylabel("Campaign")
    plt.title("Campaign Profitability")
    plt.tight_layout()
    plt.savefig(output / "campaign_roas.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=kpis, x="spend", y="revenue", size="conversions", hue="campaign", s=150)
    plt.title("Spend vs Revenue")
    plt.tight_layout()
    plt.savefig(output / "spend_vs_revenue.png", dpi=160)
    plt.close()

    total = kpis[["spend", "impressions", "clicks", "conversions", "revenue"]].sum()
    overall_ctr = total["clicks"] / total["impressions"] * 100 if total["impressions"] else 0
    overall_roas = total["revenue"] / total["spend"] if total["spend"] else 0
    strongest, weakest = ranked.iloc[0], ranked.iloc[-1]
    report = [
        "# Campaign Performance Insights", "",
        f"- Total spend: $${total['spend']:,.2f}",
        f"- Total revenue: $${total['revenue']:,.2f}",
        f"- Overall CTR: ${overall_ctr:.2f}%",
        f"- Overall ROAS: ${overall_roas:.2f}x", "",
        "## Recommendations",
        f"- Scale **${strongest.campaign}**, the strongest ROAS campaign (${strongest.roas:.2f}x).",
        f"- Review or optimize **${weakest.campaign}**, the weakest ROAS campaign (${weakest.roas:.2f}x).",
        f"- Improve creative or targeting for campaigns with CTR below ${kpis.ctr_percent.median():.2f}%, the campaign median.",
    ]
    (output / "insights.md").write_text("\n".join(report), encoding="utf-8")
    return kpis


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze social media campaign performance.")
    parser.add_argument("--input", required=True, help="Path to campaign CSV data.")
    parser.add_argument("--output", default="outputs", help="Directory for generated results.")
    args = parser.parse_args()
    data = load_campaigns(args.input)
    kpis = write_outputs(data, args.output)
    print(f"Analyzed ${len(kpis)} campaigns. Results saved to ${Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
