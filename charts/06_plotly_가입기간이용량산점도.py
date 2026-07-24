"""
가입기간(tenure_months) x 평균 데이터 사용량(data_gb) 산점도, churn_yn 색상 구분 (plotly.express)

- raw/data_customers.csv의 join_date로부터 2024-12-31 기준 가입기간(개월)을
  계산하고, raw/data_usage_history.csv에서 고객별 평균 data_gb를 계산해
  customer_id로 연결한다 (직접 재계산, 사전 계산된 숫자를 코드에 박아넣지 않음).
"""

from pathlib import Path

import pandas as pd
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"
USAGE_PATH = BASE_DIR / "raw" / "data_usage_history.csv"

REFERENCE_DATE = pd.Timestamp("2024-12-31")


def compute_joined() -> pd.DataFrame:
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig", parse_dates=["join_date"])
    usage = pd.read_csv(USAGE_PATH, encoding="utf-8-sig")

    customers["tenure_months"] = (
        (REFERENCE_DATE.year - customers["join_date"].dt.year) * 12
        + (REFERENCE_DATE.month - customers["join_date"].dt.month)
    )

    avg_data_gb = usage.groupby("customer_id")["data_gb"].mean().rename("avg_data_gb")

    df = customers.merge(avg_data_gb, on="customer_id", how="inner")
    df["churn_label"] = df["churn_yn"].map({"Y": "이탈", "N": "유지"})
    return df


def build_figure(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x="tenure_months",
        y="avg_data_gb",
        color="churn_label",
        color_discrete_map={"이탈": "#d03b3b", "유지": "#2a78d6"},
        custom_data=["customer_id", "tenure_months", "avg_data_gb", "churn_label"],
        title="가입기간 x 평균 데이터 사용량 (raw 원본 직접 집계, churn_yn 색상 구분)",
        labels={"tenure_months": "가입기간 (개월)", "avg_data_gb": "평균 데이터 사용량 (GB)", "churn_label": "이탈 여부"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "가입기간: %{customdata[1]}개월<br>"
            "평균 데이터 사용량: %{customdata[2]:.2f}GB<br>"
            "이탈 여부: %{customdata[3]}"
            "<extra></extra>"
        )
    )
    return fig


def main() -> None:
    df = compute_joined()
    build_figure(df).show()


if __name__ == "__main__":
    main()
