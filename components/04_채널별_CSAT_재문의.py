"""
채널별 CSAT 평균 x 재문의율 결합차트 (이중 y축)

- raw/data_consultations.csv와 raw/data_satisfaction.csv를 consult_id로
  연결해서 CSAT를 계산하고, raw/data_consultations.csv의 is_recontact로
  재문의율을 계산함 (둘 다 직접 재계산, 사전 계산된 표를 사용하지 않음).
- 이중 y축(dual-axis)은 두 지표의 축 스케일을 임의로 조절해 상관관계를
  실제보다 강해 보이게 왜곡할 수 있어 일반적으로는 지양되는 방식이지만,
  이 스크립트는 사용자가 명시적으로 이중 y축을 요청해 그대로 구현함.
- 관련 노트: 04_insights/i-001-채널별-재문의율.md, 04_insights/i-003-저만족도-채널요인.md
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CONSULT_PATH = BASE_DIR / "raw" / "data_consultations.csv"
SATISFACTION_PATH = BASE_DIR / "raw" / "data_satisfaction.csv"
OUTPUT_PATH = BASE_DIR / "components" / "output" / "04_채널별_CSAT_재문의.png"

# 팔레트 (dataviz 스킬 참고 팔레트): CSAT=blue(막대), 재문의율=red(선) — 뚜렷이 다른 색+마크 타입
COLOR_CSAT = "#2a78d6"
COLOR_RECONTACT = "#e34948"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글이 깨지지 않게 한다."""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def compute_channel_csat() -> pd.DataFrame:
    """data_consultations와 data_satisfaction을 consult_id로 조인해
    채널별 CSAT 평균을 직접 계산한다."""
    consultations = pd.read_csv(CONSULT_PATH, encoding="utf-8-sig")
    satisfaction = pd.read_csv(SATISFACTION_PATH, encoding="utf-8-sig")
    merged = satisfaction.merge(consultations, on="consult_id", suffixes=("_sat", "_con"))
    return merged.groupby("channel")["csat"].mean().rename("csat_mean")


def compute_channel_recontact() -> pd.DataFrame:
    """data_consultations의 is_recontact 컬럼으로 채널별 재문의율(%)을 직접 계산한다.
    CSAT 계산과 별개로 상담 원본 전체(1,320건)를 기준으로 한다."""
    consultations = pd.read_csv(CONSULT_PATH, encoding="utf-8-sig")
    total = consultations.groupby("channel").size()
    recontact = consultations[consultations["is_recontact"] == "Y"].groupby("channel").size()
    rate = (recontact / total * 100).rename("recontact_rate")
    return rate


def build_combined_table() -> pd.DataFrame:
    """CSAT 평균과 재문의율을 채널 기준으로 합치고, CSAT이 낮은 채널이
    왼쪽에 오도록 오름차순 정렬해서 반환한다."""
    csat = compute_channel_csat()
    recontact = compute_channel_recontact()
    combined = pd.concat([csat, recontact], axis=1)
    return combined.sort_values("csat_mean", ascending=True).reset_index()


def plot_combined_chart(ax_left: plt.Axes, df: pd.DataFrame) -> None:
    """왼쪽 y축엔 CSAT 평균 막대, 오른쪽 y축엔 재문의율 꺾은선을 겹쳐 그린다.
    막대(파랑)와 선(빨강)을 색과 마크 타입 모두 다르게 해서 서로 다른 지표임을
    분명히 하고, 두 지표가 채널별로 반대 방향(CSAT 낮음 <-> 재문의율 높음)으로
    움직인다는 걸 한눈에 보여준다."""
    x = range(len(df))

    bars = ax_left.bar(
        x, df["csat_mean"], color=COLOR_CSAT, width=0.5, label="CSAT 평균 (왼쪽 축)", zorder=2,
    )
    ax_left.set_ylim(0, 5)
    ax_left.set_ylabel("CSAT 평균 (5점 만점)", color=COLOR_CSAT, fontsize=10)
    ax_left.tick_params(axis="y", colors=COLOR_CSAT, labelsize=9)
    for bar, value in zip(bars, df["csat_mean"]):
        ax_left.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
            f"{value:.2f}", fontsize=9, color=COLOR_CSAT, ha="center", va="bottom",
        )

    ax_right = ax_left.twinx()
    line = ax_right.plot(
        x, df["recontact_rate"], color=COLOR_RECONTACT, linewidth=2.5,
        marker="o", markersize=7, markerfacecolor=COLOR_RECONTACT,
        markeredgecolor=COLOR_SURFACE, markeredgewidth=1.5,
        label="재문의율 (오른쪽 축)", zorder=3,
    )
    ax_right.set_ylim(0, 40)
    ax_right.set_ylabel("재문의율 (%)", color=COLOR_RECONTACT, fontsize=10)
    ax_right.tick_params(axis="y", colors=COLOR_RECONTACT, labelsize=9)

    # 왼쪽(CSAT)·오른쪽(재문의율) 축의 스케일이 달라서, 화면상 막대 라벨과 선 라벨이
    # 같은 높이에 겹치는 경우가 생긴다(0~5, 0~40이라는 서로 다른 범위를 같은 픽셀
    # 높이에 그리기 때문). 두 라벨의 상대 위치(0~1로 정규화)가 가까우면 재문의율
    # 라벨을 점 아래로 내려서 겹치지 않게 한다.
    COLLISION_THRESHOLD = 0.08
    for xi, csat_value, recontact_value in zip(x, df["csat_mean"], df["recontact_rate"]):
        csat_frac = csat_value / 5
        recontact_frac = recontact_value / 40
        if abs(csat_frac - recontact_frac) < COLLISION_THRESHOLD:
            label_y, va = recontact_value - 1.6, "top"
        else:
            label_y, va = recontact_value + 1.2, "bottom"
        ax_right.text(
            xi, label_y, f"{recontact_value:.1f}%",
            fontsize=9, color=COLOR_RECONTACT, ha="center", va=va, fontweight="bold",
        )

    ax_left.set_xticks(list(x))
    ax_left.set_xticklabels(df["channel"], color=COLOR_SECONDARY_INK, fontsize=11)
    ax_left.set_title(
        "채널별 CSAT 평균 x 재문의율 (CSAT 낮은 순, raw 원본 직접 집계)",
        loc="left", color=COLOR_PRIMARY_INK, fontsize=13, fontweight="bold", pad=14,
    )

    for spine in ("top",):
        ax_left.spines[spine].set_visible(False)
        ax_right.spines[spine].set_visible(False)
    ax_left.spines["left"].set_color(COLOR_CSAT)
    ax_left.spines["bottom"].set_color(COLOR_AXIS)
    ax_right.spines["right"].set_color(COLOR_RECONTACT)
    ax_right.spines["left"].set_visible(False)

    # 그리드는 왼쪽(CSAT) 축 기준으로만 그려서 두 축의 눈금선이 서로 어긋나
    # 헷갈리는 걸 방지한다.
    ax_left.yaxis.grid(True, color=COLOR_GRID, linewidth=1, linestyle="-", zorder=0)
    ax_left.set_axisbelow(True)

    bars_handle, bars_label = ax_left.get_legend_handles_labels()
    line_handle, line_label = ax_right.get_legend_handles_labels()
    ax_left.legend(
        bars_handle + line_handle, bars_label + line_label,
        frameon=False, loc="upper left", fontsize=9,
    )


def main() -> None:
    """전체 실행 흐름: CSAT/재문의율 각각 직접 계산 -> 채널 기준 결합 -> 이중 y축 결합차트 저장."""
    set_korean_font()
    df = build_combined_table()

    fig, ax_left = plt.subplots(figsize=(10, 6.5), facecolor=COLOR_SURFACE)
    ax_left.set_facecolor(COLOR_SURFACE)

    plot_combined_chart(ax_left, df)

    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_SURFACE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
