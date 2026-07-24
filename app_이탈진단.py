"""
고객은 왜 이탈하는가 — 이탈 원인 진단 대시보드

- charts/01~06 스크립트의 compute_*()/build_figure()를 그대로 불러와 재사용한다.
- raw/ 원본 CSV를 매번 직접 읽어 재계산한다 (숫자를 하드코딩하지 않음).
- 기존 app.py("CS 데이터 분석 대시보드", 상담원 관점 BigQuery 섹션 포함)와는
  별개의 대시보드다.
- 실행: streamlit run app_이탈진단.py
"""

import importlib.util
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "charts"
CUSTOMERS_PATH = BASE_DIR / "raw" / "data_customers.csv"


def _load_chart_module(module_name: str, filename: str):
    """charts/의 모듈을 importlib으로 안전하게 불러온다."""
    spec = importlib.util.spec_from_file_location(module_name, CHARTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_data(ttl=300, show_spinner=False)
def compute_overall_metrics() -> dict:
    """raw/data_customers.csv를 직접 읽어 전체 고객 수·이탈 고객 수·전체 이탈율을 계산한다."""
    customers = pd.read_csv(CUSTOMERS_PATH, encoding="utf-8-sig")
    total_n = len(customers)
    churn_n = int((customers["churn_yn"] == "Y").sum())
    churn_rate = churn_n / total_n * 100
    return {"total_n": total_n, "churn_n": churn_n, "churn_rate": churn_rate}


def main() -> None:
    st.set_page_config(page_title="고객은 왜 이탈하는가", layout="wide")
    st.title("고객은 왜 이탈하는가 — 이탈 원인 진단 대시보드")

    metrics = compute_overall_metrics()
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 고객 수", f"{metrics['total_n']:,}명")
    col2.metric("이탈 고객 수", f"{metrics['churn_n']:,}명")
    col3.metric("전체 이탈율", f"{metrics['churn_rate']:.1f}%")

    st.divider()

    voc_mod = _load_chart_module("voc_churn", "01_plotly_voc이탈비교.py")
    channel_mod = _load_chart_module("channel_csat_recontact", "02_plotly_채널CSAT재문의.py")
    recontact_bucket_mod = _load_chart_module("recontact_bucket_churn", "03_plotly_재문의구간이탈율.py")
    plan_mod = _load_chart_module("plan_churn", "04_plotly_요금제이탈율.py")
    region_mod = _load_chart_module("region_churn", "05_plotly_지역이탈율.py")
    tenure_usage_mod = _load_chart_module("tenure_usage_scatter", "06_plotly_가입기간이용량산점도.py")

    st.subheader("① VOC로 본 이탈")
    voc_df = voc_mod.compute_churn_rates()
    st.plotly_chart(voc_mod.build_figure(voc_df), use_container_width=True)

    st.subheader("② 채널·만족도로 본 이탈")
    channel_df = channel_mod.compute_channel_table()
    st.plotly_chart(channel_mod.build_figure(channel_df), use_container_width=True)

    st.subheader("③ 재문의 반복으로 본 이탈")
    bucket_df, overall_rate = recontact_bucket_mod.compute_bucket_churn()
    st.plotly_chart(recontact_bucket_mod.build_figure(bucket_df, overall_rate), use_container_width=True)

    st.subheader("④ 요금제로 본 이탈")
    plan_df = plan_mod.compute_plan_churn()
    st.plotly_chart(plan_mod.build_figure(plan_df), use_container_width=True)

    st.subheader("⑤ 지역으로 본 이탈")
    region_df = region_mod.compute_region_churn()
    st.plotly_chart(region_mod.build_figure(region_df), use_container_width=True)

    st.subheader("⑥ 가입기간·이용량으로 본 이탈")
    tenure_usage_df = tenure_usage_mod.compute_joined()
    st.plotly_chart(tenure_usage_mod.build_figure(tenure_usage_df), use_container_width=True)


if __name__ == "__main__":
    main()
