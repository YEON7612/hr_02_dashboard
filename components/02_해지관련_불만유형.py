"""
해지관련 부정 VOC 유형별 건수 시각화

- raw/data_voc.csv에서 category=해지관련, sentiment=부정인 행의 content를
  직접 다시 읽어 집계함 (사전 계산된 표를 사용하지 않음).
- 관련 노트: 01_questions/q-001-voc-현황.md, 04_insights/i-002-voc-불만패턴.md
"""

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "raw" / "data_voc.csv"
OUTPUT_PATH = BASE_DIR / "charts" / "02_해지관련_불만유형.png"

# 팔레트 (dataviz 스킬 참고 팔레트): 부정 VOC이므로 이전 차트와 동일하게 red slot6 재사용
COLOR_BAR = "#e34948"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"

WRAP_WIDTH = 16  # 한글 라벨 줄바꿈 기준 글자 수


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글 라벨이 깨지지 않게 한다."""
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def load_cancel_complaints() -> pd.DataFrame:
    """raw/data_voc.csv를 읽어 category=해지관련, sentiment=부정인 행만 남긴다.
    이 두 조건은 다시 계산하는 것이지 이전 결과를 재사용하지 않는다."""
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    filtered = df[(df["category"] == "해지관련") & (df["sentiment"] == "부정")]
    return filtered


def aggregate_by_content(df: pd.DataFrame) -> pd.DataFrame:
    """content(원문 문장)별 건수를 집계한다.
    막대그래프에서 건수가 많은 유형이 위쪽에 오도록, 오름차순으로 정렬해서 반환한다.
    (수평 막대그래프는 첫 행이 아래에 그려지므로, 오름차순 정렬이 '큰 값이 위'가 된다.)"""
    counts = df.groupby("content").size().reset_index(name="count")
    return counts.sort_values("count", ascending=True).reset_index(drop=True)


def wrap_label(text: str) -> str:
    """문장이 긴 content를 y축 라벨로 쓸 때 겹치지 않도록 여러 줄로 줄바꿈한다."""
    return "\n".join(textwrap.wrap(text, width=WRAP_WIDTH))


def plot_horizontal_bars(ax: plt.Axes, counts: pd.DataFrame) -> None:
    """유형별 건수를 가로 막대그래프로 그리고, 막대 끝에 건수를 직접 라벨링한다.
    단일 시리즈(건수 하나뿐)라 범례는 따로 두지 않는다."""
    y_positions = range(len(counts))
    labels = [wrap_label(text) for text in counts["content"]]

    bars = ax.barh(
        y_positions,
        counts["count"],
        color=COLOR_BAR,
        height=0.55,
    )

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels, color=COLOR_SECONDARY_INK, fontsize=10)

    # 막대 끝(값)에 건수를 직접 표시. 축 밖으로 튀지 않도록 최댓값 대비 여유 공간을 확보한다.
    max_count = counts["count"].max()
    ax.set_xlim(0, max_count * 1.18)
    for bar, count in zip(bars, counts["count"]):
        ax.text(
            bar.get_width() + max_count * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{count}건",
            va="center",
            ha="left",
            color=COLOR_PRIMARY_INK,
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title(
        "해지관련 부정 VOC 유형별 건수 (raw/data_voc.csv 기준)",
        loc="left",
        color=COLOR_PRIMARY_INK,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_AXIS)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=COLOR_MUTED, labelsize=9)
    ax.xaxis.grid(True, color=COLOR_GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)


def main() -> None:
    """전체 실행 흐름: 데이터 로드 → 필터링 → content별 집계 → 가로 막대그래프 저장."""
    set_korean_font()
    df = load_cancel_complaints()
    counts = aggregate_by_content(df)

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    plot_horizontal_bars(ax, counts)

    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_SURFACE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
