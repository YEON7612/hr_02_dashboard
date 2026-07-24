"""
번아웃(초과근무 시간) x CSAT 평균 산점도 — Plotly Express

- BigQuery `PROJECT1_DAY.agents01` ⋈ `project1_day_03.consultations_table` ⋈
  `project1_day_03.satisfaction_table`을 agent_id/consult_id로 직접 조인해 상담원별
  CSAT 평균을 재계산한다 (사전 계산된 표를 재사용하지 않음).
  프로젝트 ID는 하드코딩하지 않고 bigquery.Client()가 로컬 ADC(Application
  Default Credentials)로 인식하는 본인 프로젝트를 그대로 사용한다.
  (사전 준비: `gcloud auth application-default login` 및 해당 프로젝트에 BigQuery 접근 권한 필요)
  주의: 02_data 노트들의 source에는 `project1_day1.*`로 적혀 있으나, 실제 조회 결과 그
  데이터셋은 비어 있었고 실 데이터는 agents=`PROJECT1_DAY.agents01`,
  consultations/satisfaction=`project1_day_03.*_table`에 있었다 — 노트 갱신 필요.
- 관련 노트: 01_questions/q-009-직원만족도-고객경험.md,
  04_insights/i-004-직원만족도-고객경험.md
  (기존 노트 기준 r=-0.086, p≈0.72, n=20, 유의하지 않음 — 이 스크립트는 그 상관계수를
  원본에서 직접 재계산해서 산점도로 보여준다)
- trendline="ols"는 statsmodels 패키지가 필요하다 (requirements.txt에 추가함).
- 실행: python charts/08_plotly_번아웃CSAT산점도.py
"""

import pandas as pd
import plotly.express as px
from google.cloud import bigquery

QUERY = """
SELECT
  a.agent_id,
  a.overtime_hours_avg,
  AVG(s.csat) AS csat_mean
FROM `PROJECT1_DAY.agents01` a
JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
GROUP BY a.agent_id, a.overtime_hours_avg
"""

COLOR_MARKER = "#2a78d6"
COLOR_TRENDLINE = "#e34948"
COLOR_SURFACE = "#fcfcfb"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_MUTED = "#898781"


def load_agent_csat() -> pd.DataFrame:
    """BigQuery에서 상담원별 초과근무 시간·CSAT 평균을 직접 조인·집계해 가져온다."""
    client = bigquery.Client()
    return client.query(QUERY).to_dataframe()


def build_figure(df: pd.DataFrame):
    """산점도 + OLS 추세선을 그리고, 오른쪽 위에 상관계수(r)를 텍스트로 표시한다."""
    r = df["overtime_hours_avg"].corr(df["csat_mean"])

    fig = px.scatter(
        df,
        x="overtime_hours_avg",
        y="csat_mean",
        trendline="ols",
        hover_name="agent_id",
        hover_data={
            "overtime_hours_avg": ":.0f",
            "csat_mean": ":.2f",
        },
        labels={
            "overtime_hours_avg": "평균 초과근무 시간 (월, 시간)",
            "csat_mean": "상담원별 CSAT 평균 (5점 만점)",
        },
        title="번아웃(초과근무 시간) x CSAT 평균 (agents/consultations/satisfaction 직접 조인, BigQuery 기준)",
    )

    fig.update_traces(
        marker=dict(size=11, color=COLOR_MARKER, line=dict(width=1, color="white")),
        selector=dict(mode="markers"),
    )
    fig.update_traces(
        line=dict(color=COLOR_TRENDLINE, width=2),
        selector=dict(mode="lines"),
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        text=f"r = {r:.2f}",
        showarrow=False,
        font=dict(size=16, color=COLOR_PRIMARY_INK),
        align="right",
        bgcolor=COLOR_SURFACE,
        bordercolor=COLOR_MUTED,
        borderwidth=1,
        borderpad=6,
    )

    fig.update_layout(
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        font=dict(family="Malgun Gothic, Arial", color=COLOR_PRIMARY_INK),
        title=dict(x=0.02),
    )
    return fig


def main() -> None:
    df = load_agent_csat()
    fig = build_figure(df)
    fig.show()


if __name__ == "__main__":
    main()
