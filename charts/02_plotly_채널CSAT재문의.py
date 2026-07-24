"""
채널별 CSAT 평균 x 재문의율 결합차트 (plotly, dual-axis)

- raw/data_satisfaction.csv와 raw/data_consultations.csv를 consult_id로
  연결해 CSAT를 계산하고, raw/data_consultations.csv의 is_recontact로
  재문의율을 계산한다 (둘 다 직접 재계산, 사전 계산된 표를 사용하지 않음).
- 관련 노트: 04_insights/i-001-채널별-재문의율.md, 04_insights/i-003-저만족도-채널요인.md
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent
CONSULT_PATH = BASE_DIR / "raw" / "data_consultations.csv"
SATISFACTION_PATH = BASE_DIR / "raw" / "data_satisfaction.csv"

COLOR_CSAT = "#2a78d6"
COLOR_RECONTACT = "#e34948"


def compute_channel_table() -> pd.DataFrame:
    """consult_id로 조인해 channel별 CSAT 평균을 계산하고, data_consultations의
    is_recontact로 channel별 재문의율을 계산해 CSAT 낮은순으로 정렬해 반환한다."""
    consultations = pd.read_csv(CONSULT_PATH, encoding="utf-8-sig")
    satisfaction = pd.read_csv(SATISFACTION_PATH, encoding="utf-8-sig")

    merged = satisfaction.merge(consultations, on="consult_id", suffixes=("_sat", "_con"))
    csat_mean = merged.groupby("channel")["csat"].mean().rename("csat_mean")

    total = consultations.groupby("channel").size()
    recontact = consultations[consultations["is_recontact"] == "Y"].groupby("channel").size()
    recontact_rate = (recontact / total * 100).rename("recontact_rate")

    df = pd.concat([csat_mean, recontact_rate], axis=1).reset_index()
    return df.sort_values("csat_mean", ascending=True)


def build_figure(df: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["channel"],
            y=df["csat_mean"],
            name="CSAT 평균 (왼쪽 축)",
            marker_color=COLOR_CSAT,
            yaxis="y1",
            hovertemplate="<b>%{x}</b><br>CSAT 평균: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["channel"],
            y=df["recontact_rate"],
            name="재문의율 (오른쪽 축)",
            mode="lines+markers",
            line=dict(color=COLOR_RECONTACT, width=3),
            marker=dict(size=9, color=COLOR_RECONTACT),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>재문의율: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="채널별 CSAT 평균 x 재문의율 (CSAT 낮은 순, raw 원본 직접 집계)",
        xaxis=dict(title=""),
        yaxis=dict(title="CSAT 평균 (5점 만점)", range=[0, 5], color=COLOR_CSAT),
        yaxis2=dict(
            title="재문의율 (%)", range=[0, 40], color=COLOR_RECONTACT,
            overlaying="y", side="right",
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def main() -> None:
    df = compute_channel_table()
    build_figure(df).show()


if __name__ == "__main__":
    main()
