---
date: 2026-07-10
category: 스키마
data: data_usage_history
tags: [이용이력]
source: "[[raw/data_usage_history.csv]]"
---

## 개요

월별 이용 이력 데이터. 6,000건, 6001행(헤더 포함). 고객 500명 x 12개월(2024-01~2024-12) 구조로 보임.

## 컬럼

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| usage_id | string | 이용 이력 ID (PK) |
| customer_id | string | 고객 ID (FK) |
| year_month | string | 이용 년월. 2024-01 ~ 2024-12 |
| data_gb | float | 데이터 사용량(GB) |
| call_min | int | 통화 사용량(분) |
| billing_amount | int | 청구 금액 |
| service_count | int | 부가서비스 이용 건수 |
| app_login_count | int | 앱 로그인 횟수 |

## 연결

- `customer_id` 기준으로 [[data_customers]]와 연결된다.
