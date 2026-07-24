"""
만족도(CSAT/NPS) 현황 스코어카드

- raw/data_satisfaction.csv를 직접 읽어 계산함 (사전 계산된 표를 사용하지 않음).
- 관련 노트: 01_questions/q-004-저만족도-원인.md, 04_insights/i-003-저만족도-채널요인.md
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "raw" / "data_satisfaction.csv"
OUTPUT_PATH = BASE_DIR / "components" / "output" / "02_csat_nps_scorecard.png"

# 팔레트 (dataviz 스킬 참고 팔레트)
COLOR_PAGE = "#f9f9f7"       # 전체 배경(page plane)
COLOR_CARD = "#fcfcfb"       # 카드 배경(chart surface)
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"
COLOR_MUTED = "#898781"
COLOR_TRACK = "#e1e0d9"       # 게이지 미채움 트랙
COLOR_GOOD = "#0ca30c"        # status: good (NPS 양수)
COLOR_CRITICAL = "#d03b3b"    # status: critical (NPS 음수)


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글이 깨지지 않게 한다."""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def load_satisfaction() -> pd.DataFrame:
    """raw/data_satisfaction.csv를 읽어 DataFrame으로 반환한다. BOM 제거를 위해 utf-8-sig 사용."""
    return pd.read_csv(RAW_PATH, encoding="utf-8-sig")


def classify_nps_group(score: int) -> str:
    """NPS 원점수(0~10)를 추천자(9~10)/중립자(7~8)/비판자(0~6) 3그룹으로 분류한다."""
    if score >= 9:
        return "추천자"
    if score >= 7:
        return "중립자"
    return "비판자"


def compute_metrics(df: pd.DataFrame) -> dict:
    """스코어카드 4개 지표를 모두 계산해서 dict로 반환한다.
    ① csat_mean, ② nps_mean, ③ nps_score(추천자%-비판자%), ④ low_csat_pct를 담는다."""
    total = len(df)

    csat_mean = df["csat"].mean()

    nps_mean = df["nps"].mean()
    groups = df["nps"].apply(classify_nps_group)
    promoter_pct = (groups == "추천자").sum() / total * 100
    detractor_pct = (groups == "비판자").sum() / total * 100
    nps_score = promoter_pct - detractor_pct

    low_csat_count = df["csat"].isin([1, 2]).sum()
    low_csat_pct = low_csat_count / total * 100

    return {
        "total": total,
        "csat_mean": csat_mean,
        "nps_mean": nps_mean,
        "promoter_pct": promoter_pct,
        "detractor_pct": detractor_pct,
        "nps_score": nps_score,
        "low_csat_count": low_csat_count,
        "low_csat_pct": low_csat_pct,
    }


def draw_card_background(ax: plt.Axes) -> None:
    """카드 하나의 배경(둥근 사각형, chart surface 색)을 그린다.
    카드 사이는 선(border)이 아니라 Figure의 여백(gutter)으로만 구분한다."""
    ax.add_patch(
        FancyBboxPatch(
            (0.03, 0.03),
            0.94,
            0.94,
            boxstyle="round,pad=0,rounding_size=0.04",
            linewidth=0,
            facecolor=COLOR_CARD,
        )
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_stat_card(
    ax: plt.Axes,
    label: str,
    value_text: str,
    desc_text: str,
    value_color: str = COLOR_PRIMARY_INK,
    value_fontsize: int = 34,
    label_y: float = 0.80,
    value_y: float = 0.55,
    desc_y: float = 0.30,
) -> None:
    """카드 공통 레이아웃(라벨-작게 → 핵심 숫자-크게 → 설명-작게)을 그린다.
    value_fontsize와 value_color를 카드마다 다르게 줘서 ②는 작게(참고용),
    ③은 가장 크고 상태색으로 강조하는 식으로 위계를 만든다."""
    draw_card_background(ax)

    ax.text(
        0.08, label_y, label,
        fontsize=11, color=COLOR_SECONDARY_INK, va="center", ha="left",
    )
    ax.text(
        0.08, value_y, value_text,
        fontsize=value_fontsize, color=value_color, fontweight="bold",
        va="center", ha="left",
    )
    ax.text(
        0.08, desc_y, desc_text,
        fontsize=10, color=COLOR_MUTED, va="center", ha="left", wrap=True,
    )


def draw_nps_gauge(ax: plt.Axes, nps_score: float, status_color: str) -> None:
    """NPS 점수(-100~+100)가 전체 범위에서 어디쯤인지 보여주는 작은 게이지 바를 그린다.
    0을 중심으로 왼쪽은 음수, 오른쪽은 양수 영역이며, 0에서 현재 값까지만 상태색으로 채운다."""
    gauge_y = 0.14
    gauge_height = 0.05
    x_left, x_right = 0.08, 0.92
    x_center = (x_left + x_right) / 2

    def value_to_x(value: float) -> float:
        frac = (value + 100) / 200  # -100~100 -> 0~1
        return x_left + frac * (x_right - x_left)

    # 미채움 트랙 (-100 ~ +100 전체)
    ax.add_patch(
        Rectangle(
            (x_left, gauge_y), x_right - x_left, gauge_height,
            facecolor=COLOR_TRACK, edgecolor="none",
        )
    )

    # 0에서 현재 값까지 상태색으로 채움
    x_value = value_to_x(nps_score)
    fill_left = min(x_center, x_value)
    fill_width = abs(x_value - x_center)
    ax.add_patch(
        Rectangle(
            (fill_left, gauge_y), fill_width, gauge_height,
            facecolor=status_color, edgecolor="none",
        )
    )

    # 현재 값 위치 마커 (2px 링 효과를 흰 원으로 표현)
    marker_center_y = gauge_y + gauge_height / 2
    ax.add_patch(Circle((x_value, marker_center_y), 0.014, facecolor=status_color, edgecolor=COLOR_CARD, linewidth=2, zorder=3))

    # 0 지점 눈금선
    ax.plot([x_center, x_center], [gauge_y - 0.01, gauge_y + gauge_height + 0.01], color=COLOR_MUTED, linewidth=1, zorder=2)

    # 양 끝 값 라벨
    ax.text(x_left, gauge_y - 0.05, "-100", fontsize=8, color=COLOR_MUTED, ha="left", va="top")
    ax.text(x_right, gauge_y - 0.05, "+100", fontsize=8, color=COLOR_MUTED, ha="right", va="top")
    ax.text(x_center, gauge_y - 0.05, "0", fontsize=8, color=COLOR_MUTED, ha="center", va="top")


def main() -> None:
    """전체 실행 흐름: 데이터 로드 → 4개 지표 계산 → 4카드 스코어카드 그리기 → PNG 저장."""
    set_korean_font()
    df = load_satisfaction()
    m = compute_metrics(df)

    nps_status_color = COLOR_CRITICAL if m["nps_score"] < 0 else COLOR_GOOD
    nps_status_label = "▼ 매우 낮음 (개선 필요)" if m["nps_score"] < 0 else "▲ 양호"

    fig, axes = plt.subplots(1, 4, figsize=(16, 5), facecolor=COLOR_PAGE)
    fig.suptitle(
        "만족도(CSAT/NPS) 현황 스코어카드 (2024년, raw/data_satisfaction.csv 기준)",
        color=COLOR_PRIMARY_INK, fontsize=14, fontweight="bold", x=0.02, ha="left", y=0.98,
    )

    # ① CSAT 평균
    draw_stat_card(
        axes[0],
        label="CSAT 평균 (5점 만점)",
        value_text=f"{m['csat_mean']:.2f}",
        desc_text=f"{m['total']:,}건 만족도 설문 기준",
        value_color=COLOR_PRIMARY_INK,
        value_fontsize=34,
    )

    # ② NPS 평균 (참고용, 작게)
    draw_stat_card(
        axes[1],
        label="NPS 평균 (10점 만점) · 참고",
        value_text=f"{m['nps_mean']:.2f}",
        desc_text="0~10점 원점수 평균(참고용)",
        value_color=COLOR_SECONDARY_INK,
        value_fontsize=22,
    )

    # ③ NPS 점수 (가장 크게, 상태색 강조 + 게이지)
    draw_stat_card(
        axes[2],
        label="NPS 점수 (추천자 - 비판자)",
        value_text=f"{m['nps_score']:.1f}",
        desc_text=f"추천자 {m['promoter_pct']:.1f}% · 비판자 {m['detractor_pct']:.1f}%  {nps_status_label}",
        value_color=nps_status_color,
        value_fontsize=44,
        label_y=0.86, value_y=0.62, desc_y=0.40,
    )
    draw_nps_gauge(axes[2], m["nps_score"], nps_status_color)

    # ④ 저만족(CSAT 1~2점) 비율
    draw_stat_card(
        axes[3],
        label="저만족 비율 (CSAT 1~2점)",
        value_text=f"{m['low_csat_pct']:.1f}%",
        desc_text=f"{m['low_csat_count']:,}건 / {m['total']:,}건",
        value_color=COLOR_PRIMARY_INK,
        value_fontsize=34,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.92))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_PAGE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
