"""
지역(region)별 고객 수·이탈율 (plotly.express)

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
HIGHLIGHT_REGIONS = {"부산", "대구"}


def compute_region_churn() -> pd.DataFrame:
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")
    grouped = customers.groupby("region").agg(
        n=("customer_id", "count"),
        churn_n=("churn_yn", lambda s: (s == "Y").sum()),
    )
    grouped["churn_rate"] = grouped["churn_n"] / grouped["n"] * 100
    return grouped.reset_index().sort_values("churn_rate", ascending=False)


def build_figure(df: pd.DataFrame):
    # 캡션에 쓸 인천 표본·이탈 건수를 원본에서 직접 뽑아 문자열을 만든다(하드코딩 방지).
    incheon = df[df["region"] == "인천"].iloc[0]
    caption = (
        f"인천은 표본이 {int(incheon['n'])}건이지만 이탈 {int(incheon['churn_n'])}건뿐이라 "
        "이탈율이 낮게 보일 수 있음(참고용)."
    )

    fig = px.bar(
        df,
        x="region",
        y="churn_rate",
        color="region",
        color_discrete_map={r: (COLOR_HIGHLIGHT if r in HIGHLIGHT_REGIONS else COLOR_NEUTRAL) for r in df["region"]},
        text=df["churn_rate"].map(lambda v: f"{v:.1f}%"),
        custom_data=["n", "churn_n"],
        title="지역(region)별 이탈율 (raw 원본 직접 집계)",
        labels={"region": "지역", "churn_rate": "이탈율 (%)"},
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
    fig.update_layout(
        showlegend=False,
        yaxis_range=[0, df["churn_rate"].max() + 5],
        margin=dict(b=90),
    )
    fig.add_annotation(
        text=caption,
        xref="paper", yref="paper",
        x=0, y=-0.22,
        showarrow=False,
        font=dict(size=11, color="#898781"),
        align="left",
    )
    return fig


def main() -> None:
    df = compute_region_churn()
    build_figure(df).show()


if __name__ == "__main__":
    main()
