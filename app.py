"""
CS 데이터 분석 대시보드

- components/*.py 각각을 실행해 charts/ 에 저장된 PNG를 한 페이지에 모아 보여준다.
- 사이드바의 "차트 새로고침" 버튼을 누르면 raw/ 데이터를 다시 읽어 모든 차트를 재생성한다.
- 실행: streamlit run app.py
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "charts"
COMPONENTS_DIR = BASE_DIR / "components"
DATA_DIR = BASE_DIR / "data"

CHARTS = [
    {
        "script": "01_voc_overview.py",
        "image": "01_voc_overview.png",
        "title": "VOC 카테고리별·월별 현황",
        "note": "01_questions/q-001-voc-현황.md",
    },
    {
        "script": "02_csat_nps_scorecard.py",
        "image": "02_csat_nps_scorecard.png",
        "title": "만족도(CSAT/NPS) 스코어카드",
        "note": "01_questions/q-004-저만족도-원인.md",
    },
    {
        "script": "02_해지관련_불만유형.py",
        "image": "02_해지관련_불만유형.png",
        "title": "해지관련 부정 VOC 유형",
        "note": "04_insights/i-002-voc-불만패턴.md",
    },
    {
        "script": "03_카테고리별_저만족도.py",
        "image": "03_카테고리별_저만족도.png",
        "title": "상담 category별 CSAT 평균",
        "note": "04_insights/i-003-저만족도-채널요인.md",
    },
    {
        "script": "04_채널별_CSAT_재문의.py",
        "image": "04_채널별_CSAT_재문의.png",
        "title": "채널별 CSAT x 재문의율",
        "note": "04_insights/i-001-채널별-재문의율.md",
    },
]


def regenerate_all_charts() -> list[str]:
    """components/의 모든 시각화 스크립트를 순서대로 실행해 charts/를 최신 상태로 만든다.
    실패한 스크립트 이름을 모아서 반환한다."""
    failures = []
    for chart in CHARTS:
        script_path = COMPONENTS_DIR / chart["script"]
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(chart["script"])
    return failures


def get_bigquery_client() -> bigquery.Client:
    """Streamlit Secrets 키(배포 환경)가 존재하면 해당 서비스 계정 정보로 인증하고,
    Secrets가 없거나 로컬 환경일 경우 기존 ADC(로컬 로그인 정보) 인증으로 클라이언트를 생성합니다."""
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            project_id = creds_info.get("project_id")
            return bigquery.Client(credentials=credentials, project=project_id)
    except Exception:
        pass

    return bigquery.Client()


# ---------------------------------------------------------------------------
# 상담원 관점: 직원만족도와 고객 경험 (07~09번 차트 로직 재사용, 팀 필터 추가)
# ---------------------------------------------------------------------------

TEAM_OPTIONS = ["전체", "1팀", "2팀", "3팀"]


def _load_chart_module(module_name: str, filename: str):
    """components/의 모듈을 importlib으로 안전하게 불러옵니다."""
    spec = importlib.util.spec_from_file_location(module_name, COMPONENTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_data(ttl=300, show_spinner=False)
def _load_agent_perspective_data():
    """
    1. 먼저 BigQuery 라이브 조회를 시도합니다.
    2. 실패할 경우(인증 에러, 네트워크 에러 등) data/ 폴더의 스냅샷 CSV를 불러옵니다.
    3. (데이터, 'live' 또는 'snapshot') 형태로 결과를 반환합니다.
    """
    enps_mod = _load_chart_module("enps_scorecard", "07_plotly_직원만족도eNPS스코어카드.py")
    burnout_mod = _load_chart_module("burnout_scatter", "08_plotly_번아웃CSAT산점도.py")
    training_mod = _load_chart_module("training_compare", "09_plotly_교육이수비교.py")

    # 1. BigQuery 라이브 데이터 시도
    try:
        client = get_bigquery_client()
        
        agents_df = enps_mod.load_agents()  # agent_id, team, agent_satisfaction
        csat_df = burnout_mod.load_agent_csat()  # agent_id, overtime_hours_avg, csat_mean
        csat_df = csat_df.merge(agents_df[["agent_id", "team"]], on="agent_id")

        training_raw = client.query(
            """
            SELECT a.agent_id, a.team, a.training_completed_yn, c.is_recontact, s.csat
            FROM `PROJECT1_DAY.agents01` a
            JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
            LEFT JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
            """
        ).to_dataframe()

        return agents_df, csat_df, training_raw, "live"

    # 2. BigQuery 조회 실패 시 스냅샷 CSV 자동 로드
    except Exception:
        agents_df = pd.read_csv(DATA_DIR / "agents_snapshot.csv")
        csat_df = agents_df.rename(columns={"avg_csat": "csat_mean"})
        training_raw = pd.read_csv(DATA_DIR / "agent_consultations_snapshot.csv")

        return agents_df, csat_df, training_raw, "snapshot"


def _aggregate_training(raw_df: pd.DataFrame, training_mod) -> pd.DataFrame:
    """09번 스크립트의 build_figure()가 기대하는 형태로 직접 집계한다."""
    grouped = raw_df.groupby("training_completed_yn").agg(
        csat_mean=("csat", "mean"),
        recontact_rate=("is_recontact", lambda s: (s == True).sum() / len(s) * 100),
    )
    return grouped.reindex(training_mod.GROUP_ORDER).reset_index()


def render_agent_perspective_section() -> None:
    """"상담원 관점: 직원만족도와 고객 경험" 섹션."""
    st.header("상담원 관점: 직원만족도와 고객 경험")
    st.caption(
        "07~09번 차트와 동일한 로직(BigQuery agents/consultations/satisfaction 직접 조인)을 "
        "팀별로 필터링해서 다시 계산합니다."
    )

    team_choice = st.selectbox("팀 선택", TEAM_OPTIONS, key="agent_perspective_team")

    # 라이브/스냅샷 자동 전환 데이터 가져오기
    agents_df, csat_df, training_raw, data_mode = _load_agent_perspective_data()

    if data_mode == "snapshot":
        st.info("ℹ️ 현재 BigQuery 서버 연결 제한으로 인해 '저장된 스냅샷 데이터'를 불러왔습니다.")

    enps_mod = _load_chart_module("enps_scorecard", "07_plotly_직원만족도eNPS스코어카드.py")
    burnout_mod = _load_chart_module("burnout_scatter", "08_plotly_번아웃CSAT산점도.py")
    training_mod = _load_chart_module("training_compare", "09_plotly_교육이수비교.py")

    if team_choice == "전체":
        agents_view = agents_df
        csat_view = csat_df
        training_view_raw = training_raw
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
    st.plotly_chart(fig_enps, width="stretch")

    st.subheader("번아웃 x CSAT 산점도")
    fig_burnout = burnout_mod.build_figure(csat_view)
    st.plotly_chart(fig_burnout, width="stretch")

    st.subheader("교육 이수 여부 비교")
    training_agg = _aggregate_training(training_view_raw, training_mod)
    fig_training = training_mod.build_figure(training_agg)
    st.plotly_chart(fig_training, width="stretch")


def main() -> None:
    st.set_page_config(page_title="CS 데이터 분석 대시보드", layout="wide")
    st.title("CS 데이터 분석 대시보드")
    st.caption("raw/ 원본 5종 데이터를 기반으로 한 VOC · 만족도 · 재문의 시각화 (2024년)")

    with st.sidebar:
        st.header("설정")
        if st.button("차트 새로고침 (raw 재계산)", width="stretch"):
            with st.spinner("차트를 재생성하는 중..."):
                failures = regenerate_all_charts()
            if failures:
                st.error(f"실패: {', '.join(failures)}")
            else:
                st.success("모든 차트를 새로 생성했습니다.")
        st.markdown("---")
        st.markdown(
            "차트가 보이지 않으면 위 버튼으로 생성하거나 "
            "`python components/스크립트.py`를 직접 실행하세요."
        )

    for chart in CHARTS:
        image_path = CHARTS_DIR / chart["image"]
        st.subheader(chart["title"])
        if image_path.exists():
            st.image(str(image_path), width="stretch")
        else:
            st.warning(f"{chart['image']}가 아직 없습니다. 사이드바에서 새로고침하세요.")
        st.caption(f"관련 노트: {chart['note']}")
        st.divider()

    render_agent_perspective_section()


if __name__ == "__main__":
    main()
