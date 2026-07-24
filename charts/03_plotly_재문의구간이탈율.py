"""
재문의 횟수 구간(0회/1회/2회 이상)별 이탈율 (plotly.express)

- raw/data_consultations.csv에서 고객별 재문의(is_recontact=Y) 횟수를
  계산하고, raw/data_customers.csv의 churn_yn과 customer_id로 연결해
  직접 재계산한다 (사전 계산된 숫자를 코드에 박아넣지 않음).
- 관련 노트: 04_insights/i-006-반복재문의-이탈.md
"""

from pathlib import Path

import pandas as pd
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
CONSULT_PATH = BASE_DIR / "raw" / "data_consultations.csv"
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"

COLOR_HIGHLIGHT = "#d03b3b"
COLOR_NEUTRAL = "#c3c2b7"
COLOR_BASELINE = "#52514e"


def classify_bucket(n: int) -> str:
    if n == 0:
        return "0회"
    if n == 1:
        return "1회"
    return "2회 이상"


def compute_bucket_churn() -> tuple[pd.DataFrame, float]:
    """고객별 재문의 횟수를 3구간으로 나눠 구간별 이탈율과 전체 평균 이탈율을 계산한다."""
    consultations = pd.read_csv(CONSULT_PATH, encoding="utf-8-sig")
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")

    recontact_count = (
        consultations[consultations["is_recontact"] == "Y"]
        .groupby("customer_id")
        .size()
    )

    customers = customers.copy()
    customers["recontact_n"] = customers["customer_id"].map(recontact_count).fillna(0).astype(int)
    customers = customers[customers["customer_id"].isin(consultations["customer_id"].unique())]
    customers["bucket"] = customers["recontact_n"].apply(classify_bucket)

    grouped = customers.groupby("bucket").agg(
        n=("customer_id", "count"),
        churn_n=("churn_yn", lambda s: (s == "Y").sum()),
    )
    grouped["churn_rate"] = grouped["churn_n"] / grouped["n"] * 100
    grouped = grouped.reindex(["0회", "1회", "2회 이상"]).reset_index()

    overall_rate = (customers["churn_yn"] == "Y").sum() / len(customers) * 100
    return grouped, overall_rate


def build_figure(df: pd.DataFrame, overall_rate: float):
    fig = px.bar(
        df,
        x="bucket",
        y="churn_rate",
        color="bucket",
        color_discrete_map={
            "0회": COLOR_NEUTRAL,
            "1회": COLOR_NEUTRAL,
            "2회 이상": COLOR_HIGHLIGHT,
        },
        text=df["churn_rate"].map(lambda v: f"{v:.1f}%"),
        custom_data=["n", "churn_n"],
        title="재문의 횟수 구간별 이탈율 (raw 원본 직접 집계)",
        labels={"bucket": "재문의 횟수", "churn_rate": "이탈율 (%)"},
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>재문의 %{x}</b><br>"
            "이탈율: %{y:.1f}%<br>"
            "고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명"
            "<extra></extra>"
        ),
    )
    fig.add_hline(
        y=overall_rate,
        line_dash="dash",
        line_color=COLOR_BASELINE,
        annotation_text=f"전체 평균 이탈율 {overall_rate:.1f}%",
        annotation_position="top right",
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, df["churn_rate"].max() + 5])
    return fig


def main() -> None:
    df, overall_rate = compute_bucket_churn()
    build_figure(df, overall_rate).show()


if __name__ == "__main__":
    main()
