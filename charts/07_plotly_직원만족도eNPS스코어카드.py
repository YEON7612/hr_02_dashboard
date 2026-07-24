"""
직원만족도(eNPS) 스코어카드 — Plotly Indicator 게이지

- BigQuery `PROJECT1_DAY.agents01`을 직접 읽어 eNPS를 재계산한다 (사전 계산된 결과 재사용 안 함).
  프로젝트 ID는 하드코딩하지 않고 bigquery.Client()가 로컬 gcloud ADC(Application
  Default Credentials)로 인식하는 본인 프로젝트를 그대로 사용한다.
  (사전 준비: `gcloud auth application-default login` 및 해당 프로젝트에 BigQuery 접근 권한 필요)
  주의: 02_data/agents.md에는 source가 `project1_day1.agents`로 적혀 있으나, 실제 BigQuery를
  조회해보니 그 데이터셋(대문자 PROJECT1_DAY1)은 비어 있고 실 데이터는 `PROJECT1_DAY.agents01`에
  있었다 — 노트가 최신 상태를 반영하지 못하고 있어 확인 후 갱신이 필요하다.
- agent_satisfaction(0~10 추정, 실측 범위 2~9) 기준 promoter(9~10)/passive(7~8)/detractor(0~6)
  분류는 04_insights/i-004-직원만족도-고객경험.md, 01_questions/q-009-직원만족도-고객경험.md와 동일하게 맞춤.
- 팀별 표본이 6~7명으로 CLAUDE.md 분석 기준(표본 30건 미만은 참고용)에 못 미쳐,
  팀별 카드에는 참고용 주석을 달아 둔다.
- 실행: python charts/07_plotly_직원만족도eNPS스코어카드.py
"""

import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery

QUERY = """
SELECT agent_id, team, agent_satisfaction
FROM `PROJECT1_DAY.agents01`
"""

COLOR_CRITICAL = "#d03b3b"   # status: negative eNPS
COLOR_GOOD = "#0ca30c"       # status: positive eNPS
COLOR_NEGATIVE_BG = "#f7dcdc"  # 게이지의 마이너스(0 미만) 구간 배경
COLOR_POSITIVE_BG = "#e1e0d9"  # 게이지의 플러스(0 이상) 구간 배경
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_MUTED = "#898781"

TEAM_ORDER = ["1팀", "2팀", "3팀"]


def load_agents() -> pd.DataFrame:
    """BigQuery `project1_day1.agents`를 직접 조회해 DataFrame으로 반환한다."""
    client = bigquery.Client()
    return client.query(QUERY).to_dataframe()


def classify_enps_group(score: int) -> str:
    """agent_satisfaction 원점수를 promoter(9~10)/passive(7~8)/detractor(0~6)로 분류한다."""
    if score >= 9:
        return "promoter"
    if score >= 7:
        return "passive"
    return "detractor"


def compute_enps(df: pd.DataFrame) -> float:
    """주어진 그룹(전체 또는 팀 단위)의 eNPS(promoter% - detractor%)를 계산한다."""
    total = len(df)
    groups = df["agent_satisfaction"].apply(classify_enps_group)
    promoter_pct = (groups == "promoter").sum() / total * 100
    detractor_pct = (groups == "detractor").sum() / total * 100
    return promoter_pct - detractor_pct


def status_color(enps: float) -> str:
    """eNPS 부호에 따라 상태색(음수=critical red, 양수=good green)을 반환한다."""
    return COLOR_CRITICAL if enps < 0 else COLOR_GOOD


def add_overall_gauge(fig: go.Figure, overall_enps: float, total: int) -> None:
    """① 큰 게이지: 전체 eNPS를 -100~100 범위로 표시하고, 0 미만 구간은
    빨간 계열 배경(step)으로 칠해 마이너스 영역임을 시각적으로 강조한다."""
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=overall_enps,
            number={"suffix": "", "font": {"size": 44, "color": status_color(overall_enps)}},
            title={
                "text": f"전체 eNPS<br><span style='font-size:0.6em;color:{COLOR_MUTED}'>agents 전원 n={total}</span>",
                "font": {"size": 16, "color": COLOR_PRIMARY_INK},
            },
            gauge={
                "axis": {"range": [-100, 100], "tickcolor": COLOR_MUTED},
                "bar": {"color": status_color(overall_enps), "thickness": 0.3},
                "bgcolor": "white",
                "steps": [
                    {"range": [-100, 0], "color": COLOR_NEGATIVE_BG},
                    {"range": [0, 100], "color": COLOR_POSITIVE_BG},
                ],
                "threshold": {
                    "line": {"color": COLOR_PRIMARY_INK, "width": 2},
                    "thickness": 0.9,
                    "value": 0,
                },
            },
            domain={"x": [0, 0.55], "y": [0, 1]},
        )
    )


def add_team_cards(fig: go.Figure, team_enps: pd.Series, team_counts: pd.Series) -> None:
    """② 작은 숫자 카드 3개: 1팀·2팀·3팀 eNPS를 나란히 배치한다.
    팀별 표본이 30건 미만이라 CLAUDE.md 분석 기준상 참고용이므로 카드 제목에 표시한다."""
    x_slots = [(0.62, 0.75), (0.77, 0.90), (0.92, 1.0)]

    for team, (x0, x1) in zip(TEAM_ORDER, x_slots):
        enps = team_enps[team]
        n = team_counts[team]
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=enps,
                number={"font": {"size": 30, "color": status_color(enps)}},
                title={
                    "text": f"{team} eNPS<br><span style='font-size:0.6em;color:{COLOR_MUTED}'>n={n} (참고용, &lt;30)</span>",
                    "font": {"size": 13, "color": COLOR_PRIMARY_INK},
                },
                domain={"x": [x0, x1], "y": [0.35, 0.75]},
            )
        )


def build_figure(df: pd.DataFrame) -> go.Figure:
    """전체 실행 흐름: eNPS 전체·팀별 계산 -> 큰 게이지 + 작은 카드 3개로 구성된 스코어카드 생성."""
    overall_enps = compute_enps(df)
    team_enps = df.groupby("team").apply(compute_enps)
    team_counts = df.groupby("team").size()

    fig = go.Figure()
    add_overall_gauge(fig, overall_enps, total=len(df))
    add_team_cards(fig, team_enps, team_counts)

    fig.update_layout(
        title={
            "text": "직원만족도(eNPS) 스코어카드 (BigQuery project1_day1.agents 기준)",
            "x": 0.02,
            "font": {"size": 18, "color": COLOR_PRIMARY_INK},
        },
        paper_bgcolor="#fcfcfb",
        font={"family": "Malgun Gothic, Arial", "color": COLOR_PRIMARY_INK},
        height=420,
        margin=dict(l=40, r=40, t=100, b=20),
    )
    return fig


def main() -> None:
    df = load_agents()
    fig = build_figure(df)
    fig.show()


if __name__ == "__main__":
    main()
