"""
요금제(plan)별 고객 수·이탈율 (plotly.express)

- raw/data_customers.csv를 직접 읽어 계산한다 (사전 계산된 숫자를 코드에
  박아넣지 않음).
"""

from pathlib import Path

import pandas as pd
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"

COLOR_HIGHLIGHT = "#d03b3b"
COLOR_NEUTRAL = "#c3c2b7"


def compute_plan_churn() -> pd.DataFrame:
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")
    grouped = customers.groupby("plan").agg(
        n=("customer_id", "count"),
        churn_n=("churn_yn", lambda s: (s == "Y").sum()),
    )
    grouped["churn_rate"] = grouped["churn_n"] / grouped["n"] * 100
    return grouped.reset_index()


def build_figure(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="plan",
        y="churn_rate",
        color="plan",
        color_discrete_map={p: (COLOR_HIGHLIGHT if p == "베이직" else COLOR_NEUTRAL) for p in df["plan"]},
        text=df["churn_rate"].map(lambda v: f"{v:.1f}%"),
        custom_data=["n", "churn_n"],
        title="요금제(plan)별 이탈율 (raw 원본 직접 집계)",
        labels={"plan": "요금제", "churn_rate": "이탈율 (%)"},
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "이탈율: %{y:.1f}%<br>"
            "고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명"
            "<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, df["churn_rate"].max() + 5])
    return fig


def main() -> None:
    df = compute_plan_churn()
    build_figure(df).show()


if __name__ == "__main__":
    main()
