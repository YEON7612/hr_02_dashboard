"""
전체 고객 이탈율 x 해지관련 부정 VOC 이력 고객 이탈율 비교 (plotly.express)

- raw/data_voc.csv와 raw/data_customers.csv를 customer_id로 연결해
  직접 재계산한다 (사전 계산된 숫자를 코드에 박아넣지 않음).
- 관련 노트: 04_insights/i-002-voc-불만패턴.md
"""

from pathlib import Path

import pandas as pd
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
VOC_PATH = BASE_DIR / "raw" / "data_voc.csv"
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"

COLOR_HIGHLIGHT = "#d03b3b"
COLOR_NEUTRAL = "#c3c2b7"


def compute_churn_rates() -> pd.DataFrame:
    """raw 원본을 직접 읽어 전체 고객 이탈율과, 해지관련 부정 VOC 이력이 있는
    고객의 이탈율을 각각 계산한다."""
    voc = pd.read_csv(VOC_PATH, encoding="utf-8-sig")
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")

    target_ids = voc.loc[
        (voc["category"] == "해지관련") & (voc["sentiment"] == "부정"), "customer_id"
    ].unique()

    total_n = len(customers)
    total_churn_n = int((customers["churn_yn"] == "Y").sum())
    total_rate = total_churn_n / total_n * 100

    target_customers = customers[customers["customer_id"].isin(target_ids)]
    target_n = len(target_customers)
    target_churn_n = int((target_customers["churn_yn"] == "Y").sum())
    target_rate = target_churn_n / target_n * 100

    return pd.DataFrame(
        {
            "group": ["전체 고객", "해지관련 부정 VOC 이력 있음"],
            "n": [total_n, target_n],
            "churn_n": [total_churn_n, target_churn_n],
            "churn_rate": [total_rate, target_rate],
        }
    )


def build_figure(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="group",
        y="churn_rate",
        color="group",
        color_discrete_map={
            "전체 고객": COLOR_NEUTRAL,
            "해지관련 부정 VOC 이력 있음": COLOR_HIGHLIGHT,
        },
        text=df["churn_rate"].map(lambda v: f"{v:.1f}%"),
        custom_data=["n", "churn_n"],
        title="전체 고객 vs 해지관련 부정 VOC 이력 고객 이탈율 (raw 원본 직접 집계)",
        labels={"group": "", "churn_rate": "이탈율 (%)"},
    )

    # 툴팁에 고객 수(n)와 이탈 고객 수(churn_n)를 함께 표시한다.
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
    df = compute_churn_rates()
    build_figure(df).show()


if __name__ == "__main__":
    main()
