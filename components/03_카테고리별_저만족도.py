"""
상담 category별 CSAT 평균 시각화

- raw/data_consultations.csv와 raw/data_satisfaction.csv를 consult_id로
  연결해서 직접 계산함 (사전 계산된 표를 사용하지 않음).
- 관련 노트: 01_questions/q-004-저만족도-원인.md, 04_insights/i-003-저만족도-채널요인.md
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CONSULT_PATH = BASE_DIR / "raw" / "data_consultations.csv"
SATISFACTION_PATH = BASE_DIR / "raw" / "data_satisfaction.csv"
OUTPUT_PATH = BASE_DIR / "components" / "output" / "03_카테고리별_저만족도.png"

# 팔레트 (dataviz 스킬 참고 팔레트): 저만족 강조=critical red, 나머지=중립 회색
COLOR_HIGHLIGHT = "#d03b3b"
COLOR_NEUTRAL = "#c3c2b7"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"

N_HIGHLIGHT = 2  # CSAT 평균이 가장 낮은 상위 N개 카테고리를 강조색으로 표시


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글이 깨지지 않게 한다."""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def load_joined() -> pd.DataFrame:
    """data_consultations와 data_satisfaction을 consult_id로 조인해 반환한다.
    category와 csat이 같은 행에 있어야 category별 평균을 계산할 수 있어서 조인이 필요하다."""
    consultations = pd.read_csv(CONSULT_PATH, encoding="utf-8-sig")
    satisfaction = pd.read_csv(SATISFACTION_PATH, encoding="utf-8-sig")
    return satisfaction.merge(consultations, on="consult_id", suffixes=("_sat", "_con"))


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """category별 CSAT 평균과 건수를 집계한다.
    막대그래프에서 가장 낮은 카테고리가 왼쪽에 오도록 오름차순 정렬해서 반환한다."""
    grouped = df.groupby("category").agg(
        csat_mean=("csat", "mean"),
        count=("csat", "count"),
    )
    return grouped.sort_values("csat_mean", ascending=True).reset_index()


def plot_category_csat(ax: plt.Axes, cat_df: pd.DataFrame, overall_mean: float) -> None:
    """category별 CSAT 평균 막대그래프를 그린다.
    CSAT이 가장 낮은 N_HIGHLIGHT개 카테고리는 강조색, 나머지는 중립 회색으로 칠해
    '개선이 시급한 카테고리'가 한눈에 보이게 한다. 막대 위에는 건수를 작게 표시해
    표본이 충분한지 바로 확인할 수 있게 한다."""
    x = range(len(cat_df))
    colors = [
        COLOR_HIGHLIGHT if i < N_HIGHLIGHT else COLOR_NEUTRAL
        for i in range(len(cat_df))
    ]

    bars = ax.bar(x, cat_df["csat_mean"], color=colors, width=0.6)

    # 전체 평균 기준선: 이 선보다 낮은 막대가 곧 '평균 이하' 카테고리다.
    # 라벨은 막대 영역 바깥(오른쪽 여백)에 둬서 마지막 막대의 건수 라벨과 겹치지 않게 한다.
    ax.axhline(
        overall_mean,
        color=COLOR_SECONDARY_INK,
        linewidth=1.5,
        linestyle="--",
        zorder=1,
    )
    ax.set_xlim(-0.6, len(cat_df) - 1 + 1.1)
    ax.text(
        len(cat_df) - 1 + 0.55,
        overall_mean + 0.04,
        f"전체 평균 {overall_mean:.2f}",
        fontsize=10,
        color=COLOR_SECONDARY_INK,
        ha="left",
        va="bottom",
    )

    # 막대 위에 건수(표본 확인용)를 작게 라벨링.
    # 막대 높이가 평균선에 바짝 붙어 있으면 라벨이 점선과 겹치므로,
    # 그 경우엔 평균선 위로 한 번 더 띄워서 겹치지 않게 한다.
    label_gap = 0.05
    for bar, count in zip(bars, cat_df["count"]):
        label_y = bar.get_height() + label_gap
        if label_y < overall_mean + 0.12:
            label_y = overall_mean + 0.12
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            label_y,
            f"n={count}",
            fontsize=9,
            color=COLOR_MUTED,
            ha="center",
            va="bottom",
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(cat_df["category"], color=COLOR_SECONDARY_INK, fontsize=11)
    ax.set_ylim(0, cat_df["csat_mean"].max() + 0.6)
    ax.set_ylabel("CSAT 평균 (5점 만점)", color=COLOR_SECONDARY_INK, fontsize=10)

    ax.set_title(
        "상담 category별 CSAT 평균 (낮은 순, raw 원본 직접 집계)",
        loc="left",
        color=COLOR_PRIMARY_INK,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COLOR_AXIS)
    ax.spines["bottom"].set_color(COLOR_AXIS)
    ax.tick_params(axis="both", colors=COLOR_MUTED, labelsize=9)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)


def main() -> None:
    """전체 실행 흐름: 조인 → category별 집계 → 전체 평균 계산 → 막대그래프 저장."""
    set_korean_font()
    df = load_joined()
    cat_df = aggregate_by_category(df)
    overall_mean = df["csat"].mean()

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    plot_category_csat(ax, cat_df, overall_mean)

    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_SURFACE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
