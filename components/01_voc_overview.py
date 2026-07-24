"""
VOC 카테고리별·월별 현황 시각화

- raw/data_voc.csv를 직접 읽어 집계함 (사전 계산된 표를 사용하지 않음).
- 관련 노트: 01_questions/q-001-voc-현황.md, 04_insights/i-002-voc-불만패턴.md
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "raw" / "data_voc.csv"
OUTPUT_PATH = BASE_DIR / "charts" / "01_voc_overview.png"

# 팔레트 (dataviz 스킬 참고 팔레트: 전체=blue slot1, 부정=red slot6)
COLOR_TOTAL = "#2a78d6"
COLOR_NEGATIVE = "#e34948"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY_INK = "#0b0b0b"
COLOR_SECONDARY_INK = "#52514e"


def set_korean_font() -> None:
    """matplotlib 전역 폰트를 맑은 고딕으로 설정해 한글 라벨이 네모(□)로 깨지는 걸 막는다.
    axes.unicode_minus도 함께 꺼서 마이너스 부호가 깨지는 걸 방지한다.
    added by kim yumin 20260714
    """
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def load_voc() -> pd.DataFrame:
    """raw/data_voc.csv를 읽어 DataFrame으로 반환한다.
    BOM 제거를 위해 utf-8-sig로 읽고, received_date를 날짜형으로 변환한 뒤
    월별 집계에 쓸 year_month(YYYY-MM) 컬럼을 추가한다."""
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    df["received_date"] = pd.to_datetime(df["received_date"])
    df["year_month"] = df["received_date"].dt.strftime("%Y-%m")
    return df


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """category별 전체 건수와 부정(sentiment=부정) 건수를 집계한다.
    부정 건수가 많은 카테고리가 먼저 오도록 내림차순 정렬해서 반환한다."""
    grouped = df.groupby("category").agg(
        total=("voc_id", "count"),
        negative=("sentiment", lambda s: (s == "부정").sum()),
    )
    return grouped.sort_values("negative", ascending=False)


def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """year_month(YYYY-MM)별 전체 건수와 부정 건수를 집계한다.
    시계열 그래프에 쓸 것이므로 월 순서(오름차순)로 정렬해서 반환한다."""
    grouped = df.groupby("year_month").agg(
        total=("voc_id", "count"),
        negative=("sentiment", lambda s: (s == "부정").sum()),
    )
    return grouped.sort_index()


def style_axes(ax: plt.Axes) -> None:
    """막대/꺾은선 그래프 공통 스타일을 적용한다.
    위·오른쪽·왼쪽 테두리(spine)를 지우고, y축 그리드만 옅은 회색 실선으로 그려
    데이터(막대·선)가 아닌 축·격자가 시각적으로 튀지 않게(recessive) 만든다."""
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_AXIS)
    ax.tick_params(axis="both", colors=COLOR_MUTED, labelsize=9)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)


def plot_category_bars(ax: plt.Axes, cat_df: pd.DataFrame) -> None:
    """① category별 전체 건수·부정 건수를 그룹 막대그래프로 그린다.
    전체 건수는 기본색(파랑), 부정 건수는 강조색(빨강)으로 구분해
    카테고리마다 어디서 부정 비중이 큰지 한눈에 비교할 수 있게 한다."""
    x = range(len(cat_df))
    width = 0.36

    ax.bar(
        [i - width / 2 for i in x],
        cat_df["total"],
        width=width,
        color=COLOR_TOTAL,
        label="전체 건수",
    )
    ax.bar(
        [i + width / 2 for i in x],
        cat_df["negative"],
        width=width,
        color=COLOR_NEGATIVE,
        label="부정 건수",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(cat_df.index, color=COLOR_SECONDARY_INK)
    ax.set_title(
        "① category별 전체 건수 · 부정 건수",
        loc="left",
        color=COLOR_PRIMARY_INK,
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    style_axes(ax)


def plot_monthly_lines(ax: plt.Axes, month_df: pd.DataFrame) -> None:
    """② 월별 전체 건수·부정 건수 추이를 꺾은선그래프로 그린다.
    막대그래프와 동일하게 전체=파랑, 부정=빨강 색을 재사용해
    위 그래프와 아래 그래프의 색 의미가 헷갈리지 않게 한다."""
    x = range(len(month_df))

    ax.plot(
        x,
        month_df["total"],
        color=COLOR_TOTAL,
        linewidth=2,
        marker="o",
        markersize=5,
        markerfacecolor=COLOR_TOTAL,
        markeredgecolor=COLOR_SURFACE,
        markeredgewidth=1,
        label="전체 건수",
    )
    ax.plot(
        x,
        month_df["negative"],
        color=COLOR_NEGATIVE,
        linewidth=2,
        marker="o",
        markersize=5,
        markerfacecolor=COLOR_NEGATIVE,
        markeredgecolor=COLOR_SURFACE,
        markeredgewidth=1,
        label="부정 건수",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(month_df.index, color=COLOR_SECONDARY_INK, rotation=45, ha="right")
    ax.set_title(
        "② 월별 전체 건수 · 부정 건수 추이",
        loc="left",
        color=COLOR_PRIMARY_INK,
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    style_axes(ax)


def main() -> None:
    """전체 실행 흐름을 담당한다:
    데이터 로드 → 두 종류 집계 → 2행짜리 Figure에 ①②를 각각 그리기 → PNG로 저장.
    이 스크립트를 직접 실행했을 때(entry point) 호출되는 함수다."""
    set_korean_font()
    df = load_voc()
    cat_df = aggregate_by_category(df)
    month_df = aggregate_by_month(df)

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, figsize=(10, 10), facecolor=COLOR_SURFACE
    )
    fig.suptitle(
        "VOC 카테고리별·월별 현황 (2024년, raw/data_voc.csv 기준)",
        color=COLOR_PRIMARY_INK,
        fontsize=14,
        fontweight="bold",
        x=0.02,
        ha="left",
    )

    ax_top.set_facecolor(COLOR_SURFACE)
    ax_bottom.set_facecolor(COLOR_SURFACE)

    plot_category_bars(ax_top, cat_df)
    plot_monthly_lines(ax_bottom, month_df)

    fig.tight_layout(rect=(0, 0, 1, 0.95))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, facecolor=COLOR_SURFACE)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
