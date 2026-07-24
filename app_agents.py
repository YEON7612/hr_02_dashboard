"""
상담원 관점 대시보드 (Streamlit)

- 직원만족도(eNPS)·번아웃·교육이수와 고객경험(CSAT·재문의율)의 관계를 팀별로
  뜯어보는 상담원 전용 대시보드. app.py와는 별개의 독립 대시보드다.
- charts/07~09_plotly_*.py 스크립트의 계산 로직(BigQuery 직접 조인)을 그대로
  재사용한다 — 파일명이 숫자+한글이라 일반 import 대신 importlib로 로드한다.
- 관련 노트: 01_questions/q-009-직원만족도-고객경험.md,
  04_insights/i-004-직원만족도-고객경험.md
- 실행: streamlit run app_agents.py
"""

import importlib.util
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "charts"

TEAM_OPTIONS = ["전체", "1팀", "2팀", "3팀"]


def _load_chart_module(module_name: str, filename: str):
    """charts/의 숫자+한글 파일명은 일반 import 문으로 불러올 수 없어 importlib로
    파일 경로 기준 직접 로드한다. __name__이 '__main__'이 아니므로 각 스크립트의
    fig.show() 진입점(main())은 실행되지 않고 함수만 재사용된다."""
    spec = importlib.util.spec_from_file_location(module_name, CHARTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_data(ttl=300, show_spinner=False)
def _load_agent_data():
    """07/08 스크립트와 동일한 BigQuery 조인으로 상담원 단위 데이터를 가져오고,
    교육이수 비교용 원본(상담 단위)도 함께 가져온다 (팀 필터를 로컬에서 하기 위함)."""
    enps_mod = _load_chart_module("enps_scorecard", "07_plotly_직원만족도eNPS스코어카드.py")
    burnout_mod = _load_chart_module("burnout_scatter", "08_plotly_번아웃CSAT산점도.py")

    agents_df = enps_mod.load_agents()  # agent_id, team, agent_satisfaction
    csat_df = burnout_mod.load_agent_csat()  # agent_id, overtime_hours_avg, csat_mean
    csat_df = csat_df.merge(agents_df[["agent_id", "team"]], on="agent_id")

    from google.cloud import bigquery

    client = bigquery.Client()
    training_raw = client.query(
        """
        SELECT a.agent_id, a.team, a.training_completed_yn, c.is_recontact, s.csat
        FROM `PROJECT1_DAY.agents01` a
        JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
        LEFT JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
        """
    ).to_dataframe()

    return agents_df, csat_df, training_raw


def _aggregate_training(raw_df: pd.DataFrame, training_mod) -> pd.DataFrame:
    """09번 스크립트의 build_figure()가 기대하는 형태(Y/N 2행, csat_mean/recontact_rate)로
    상담 단위 원본을 직접 재집계한다."""
    grouped = raw_df.groupby("training_completed_yn").agg(
        csat_mean=("csat", "mean"),
        recontact_rate=("is_recontact", lambda s: (s == True).sum() / len(s) * 100),
    )
    return grouped.reindex(training_mod.GROUP_ORDER).reset_index()


def main() -> None:
    st.set_page_config(page_title="상담원 관점 대시보드", layout="wide")
    st.title("상담원 관점 대시보드")
    st.caption(
        "직원만족도(eNPS)·번아웃·교육이수와 고객경험(CSAT·재문의율)의 관계를 팀별로 "
        "뜯어봅니다 (BigQuery agents/consultations/satisfaction 직접 조인, 사전 계산된 표 재사용 안 함)"
    )

    team_choice = st.selectbox("팀 선택", TEAM_OPTIONS, key="agent_dashboard_team")

    enps_mod = _load_chart_module("enps_scorecard", "07_plotly_직원만족도eNPS스코어카드.py")
    burnout_mod = _load_chart_module("burnout_scatter", "08_plotly_번아웃CSAT산점도.py")
    training_mod = _load_chart_module("training_compare", "09_plotly_교육이수비교.py")

    try:
        with st.spinner("BigQuery에서 상담원 데이터를 불러오는 중..."):
            agents_df, csat_df, training_raw = _load_agent_data()
    except Exception as exc:
        st.error(f"BigQuery 조회에 실패했습니다: {exc}")
        st.caption("`gcloud auth application-default login`으로 인증했는지 확인하세요.")
        return

    if team_choice == "전체":
        agents_view, csat_view, training_view_raw = agents_df, csat_df, training_raw
    else:
        agents_view = agents_df[agents_df["team"] == team_choice]
        csat_view = csat_df[csat_df["team"] == team_choice]
        training_view_raw = training_raw[training_raw["team"] == team_choice]
        st.caption(
            f"⚠️ {team_choice} 표본은 {len(agents_view)}명으로 CLAUDE.md 분석 기준(30건 미만)에 "
            "못 미칩니다 — 참고용으로만 보세요."
        )

    st.subheader("eNPS 스코어카드")
    if team_choice == "전체":
        fig_enps = enps_mod.build_figure(agents_view)
    else:
        team_enps_value = enps_mod.compute_enps(agents_view)
        fig_enps = go.Figure()
        enps_mod.add_overall_gauge(fig_enps, team_enps_value, total=len(agents_view))
        fig_enps.update_layout(
            title=dict(text=f"{team_choice} eNPS", x=0.02, font=dict(size=18, color=enps_mod.COLOR_PRIMARY_INK)),
            paper_bgcolor=burnout_mod.COLOR_SURFACE,
            font=dict(family="Malgun Gothic, Arial", color=enps_mod.COLOR_PRIMARY_INK),
            height=340,
            margin=dict(l=40, r=40, t=90, b=20),
        )
    st.plotly_chart(fig_enps, use_container_width=True)

    st.subheader("번아웃 x CSAT 산점도")
    fig_burnout = burnout_mod.build_figure(csat_view)
    st.plotly_chart(fig_burnout, use_container_width=True)

    st.subheader("교육 이수 여부 비교")
    training_agg = _aggregate_training(training_view_raw, training_mod)
    fig_training = training_mod.build_figure(training_agg)
    st.plotly_chart(fig_training, use_container_width=True)

    st.divider()
    st.caption(
        "관련 노트: 01_questions/q-009-직원만족도-고객경험.md, "
        "04_insights/i-004-직원만족도-고객경험.md"
    )


if __name__ == "__main__":
    main()
