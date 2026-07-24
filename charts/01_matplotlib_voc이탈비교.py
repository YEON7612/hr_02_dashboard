"""
전체 고객 이탈율 x 해지관련 부정 VOC 이력 고객 이탈율 비교 (matplotlib)

- raw/data_voc.csv와 raw/data_customers.csv를 customer_id로 연결해
  직접 재계산한다 (사전 계산된 숫자를 코드에 박아넣지 않음).
- 관련 노트: 04_insights/i-002-voc-불만패턴.md
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
VOC_PATH = BASE_DIR / "raw" / "data_voc.csv"
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"
OUTPUT_PATH = BASE_DIR / "charts" / "output" / "01_matplotlib_voc이탈비교.png"

# 팔레트 (dataviz 스킬 참고 팔레트): 강조=critical red, 나머지=중립 회색
COLOR_HIGHLIGHT = "#d03b3b"
COLOR_NEUTRAL = "#c3c2b7"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글이 깨지지 않게 한다."""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def compute_churn_rates() -> pd.DataFrame:
    """raw 원본을 직접 읽어 전체 고객 이탈율과, 해지관련 부정 VOC 이력이 있는
    고객의 이탈율을 각각 계산한다."""
    voc = pd.read_csv(VOC_PATH, encoding="utf-8-sig")
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")

    target_ids = voc.loc[
        (voc["category"] == "해지관련") & (voc["sentiment"] == "부정"), "customer_id"
    ].unique()

    total_n = len(customers)
    total_churn_n = (customers["churn_yn"] == "Y").sum()
    total_rate = total_churn_n / total_n * 100

    target_customers = customers[customers["customer_id"].isin(target_ids)]
    target_n = len(target_customers)
    target_churn_n = (target_customers["churn_yn"] == "Y").sum()
    target_rate = target_churn_n / target_n * 100

    return pd.DataFrame(
        {
            "group": ["전체 고객", "해지관련 부정 VOC 이력 있음"],
            "n": [total_n, target_n],
            "churn_n": [total_churn_n, target_churn_n],
            "churn_rate": [total_rate, target_rate],
        }
    )


def plot_comparison(ax: plt.Axes, df: pd.DataFrame) -> None:
    """두 그룹의 이탈율 막대그래프를 그린다. 두 번째 막대(해지관련 부정 VOC
    이력 있음)만 강조색으로 칠해 대비를 분명히 하고, 막대 위에는 퍼센트를 표시한다."""
    x = range(len(df))
    colors = [COLOR_NEUTRAL, COLOR_HIGHLIGHT]

    bars = ax.bar(x, df["churn_rate"], color=colors, width=0.5)

    for bar, rate, n, churn_n in zip(bars, df["churn_rate"], df["n"], df["churn_n"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
            f"{rate:.1f}%", fontsize=16, color=COLOR_PRIMARY_INK,
            fontweight="bold", ha="center", va="bottom",
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
            f"n={n}\n(이탈 {churn_n}명)", fontsize=9, color=COLOR_SURFACE,
            ha="center", va="center",
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(df["group"], color=COLOR_SECONDARY_INK, fontsize=12)
    ax.set_ylim(0, df["churn_rate"].max() + 5)
    ax.set_ylabel("이탈율 (%)", color=COLOR_SECONDARY_INK, fontsize=10)
    ax.set_title(
        "전체 고객 vs 해지관련 부정 VOC 이력 고객 이탈율 (raw 원본 직접 집계)",
        loc="left", color=COLOR_PRIMARY_INK, fontsize=13, fontweight="bold", pad=14,
    )

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COLOR_AXIS)
    ax.spines["bottom"].set_color(COLOR_AXIS)
    ax.tick_params(axis="both", colors=COLOR_SECONDARY_INK, labelsize=9)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)


def main() -> None:
    """전체 실행 흐름: raw 직접 집계 -> 이탈율 비교 -> 막대그래프 저장."""
    set_korean_font()
    df = compute_churn_rates()

    fig, ax = plt.subplots(figsize=(7, 6), facecolor=COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    plot_comparison(ax, df)

    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_SURFACE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
