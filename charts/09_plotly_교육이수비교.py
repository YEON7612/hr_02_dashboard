"""
교육 이수 여부(training_completed_yn) 그룹 비교 — CSAT 평균 x 재문의율 평균 (Plotly Subplots)

- BigQuery `PROJECT1_DAY.agents01` ⋈ `project1_day_03.consultations_table` ⋈
  `project1_day_03.satisfaction_table`을 agent_id/consult_id로 직접 조인해 Y/N
  그룹별 CSAT 평균·재문의율 평균을 재계산한다 (사전 계산된 표를 재사용하지 않음).
  프로젝트 ID는 하드코딩하지 않고 bigquery.Client()가 로컬 ADC(Application
  Default Credentials)로 인식하는 본인 프로젝트를 그대로 사용한다.
  (사전 준비: `gcloud auth application-default login` 및 해당 프로젝트에 BigQuery 접근 권한 필요)
- 관련 노트: 01_questions/q-009-직원만족도-고객경험.md,
  04_insights/i-004-직원만족도-고객경험.md
  (2026-07-23 기준 문서값: CSAT Y 3.346 vs N 3.284, 재문의율 Y 21.15% vs N 21.96%,
  point-biserial r로 봤을 때 둘 다 통계적으로 유의하지 않음 — 이 스크립트는 그 값을
  라이브 데이터에서 다시 계산해 나란히 비교한다)
- 실행: python charts/09_plotly_교육이수비교.py
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery

QUERY = """
SELECT
  a.training_completed_yn,
  AVG(s.csat) AS csat_mean,
  COUNTIF(c.is_recontact) / COUNT(*) * 100 AS recontact_rate
FROM `PROJECT1_DAY.agents01` a
JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
LEFT JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
GROUP BY a.training_completed_yn
"""

COLOR_HIGHLIGHT = "#2a78d6"   # Y(이수) 강조색
COLOR_NEUTRAL = "#c3c2b7"     # N(미이수) 회색 계열
COLOR_SURFACE = "#fcfcfb"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_MUTED = "#898781"

GROUP_ORDER = [True, False]
GROUP_LABEL = {True: "Y (이수)", False: "N (미이수)"}


def load_training_groups() -> pd.DataFrame:
    """BigQuery에서 training_completed_yn 그룹별 CSAT 평균·재문의율을 직접 조인·집계해 가져온다."""
    client = bigquery.Client()
    df = client.query(QUERY).to_dataframe()
    df["training_completed_yn"] = df["training_completed_yn"].astype(bool)
    # 주의: `.loc[[True, False]]`는 불리언 인덱스 위에서 라벨 선택이 아니라
    # 불리언 마스크로 해석되어 버리므로(pandas 특성), 반드시 `.reindex()`를 써야 한다.
    return df.set_index("training_completed_yn").reindex(GROUP_ORDER).reset_index()


def build_figure(df: pd.DataFrame) -> go.Figure:
    """왼쪽 패널: CSAT 평균 Y/N 막대, 오른쪽 패널: 재문의율 평균 Y/N 막대를 나란히 배치한다.
    Y(이수)는 강조색, N(미이수)은 회색 계열로 칠해 두 그룹을 구분하고,
    막대 위에 정확한 값을 직접 라벨링한다."""
    labels = [GROUP_LABEL[v] for v in df["training_completed_yn"]]
    colors = [COLOR_HIGHLIGHT if v else COLOR_NEUTRAL for v in df["training_completed_yn"]]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("CSAT 평균 (5점 만점)", "재문의율 평균 (%)"),
    )

    fig.add_trace(
        go.Bar(
            x=labels,
            y=df["csat_mean"],
            marker_color=colors,
            text=[f"{v:.2f}" for v in df["csat_mean"]],
            textposition="outside",
            showlegend=False,
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Bar(
            x=labels,
            y=df["recontact_rate"],
            marker_color=colors,
            text=[f"{v:.1f}%" for v in df["recontact_rate"]],
            textposition="outside",
            showlegend=False,
        ),
        row=1, col=2,
    )

    fig.update_yaxes(title_text="CSAT 평균", range=[0, df["csat_mean"].max() * 1.25], row=1, col=1)
    fig.update_yaxes(title_text="재문의율 (%)", range=[0, df["recontact_rate"].max() * 1.25], row=1, col=2)

    fig.update_annotations(font=dict(size=13, color=COLOR_PRIMARY_INK))

    fig.update_layout(
        title=dict(
            text="교육 이수 여부(Y/N)별 CSAT 평균 x 재문의율 (agents/consultations/satisfaction 직접 조인, BigQuery 기준)",
            x=0.02,
        ),
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        font=dict(family="Malgun Gothic, Arial", color=COLOR_PRIMARY_INK),
        margin=dict(t=90, b=40, l=50, r=30),
    )
    return fig


def main() -> None:
    df = load_training_groups()
    fig = build_figure(df)
    fig.show()


if __name__ == "__main__":
    main()
