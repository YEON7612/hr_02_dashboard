---
date: 2026-07-10
category: 스키마
data: data_customers
tags: [고객마스터]
source: "[[raw/data_customers.csv]]"
---

## 개요

고객 마스터 데이터. 500명, 501행(헤더 포함).

## 컬럼

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| customer_id | string | 고객 ID (PK). 다른 테이블과 연결되는 기준 키 |
| name | string | 고객명 |
| age | int | 나이 |
| gender | string | 성별. 값: 남, 여 |
| region | string | 거주 지역. 값: 서울, 경기, 인천, 부산, 대구, 기타 |
| plan | string | 가입 요금제. 값: 베이직, 스탠다드, 프리미엄 |
| join_date | date | 가입일 |
| churn_yn | string | 이탈 여부. 값: Y, N |
| churn_date | date | 이탈일. churn_yn이 N이면 비어있음 |

## 연결

- `customer_id` 기준으로 [[data_voc]], [[data_consultations]], [[data_satisfaction]], [[data_usage_history]]와 연결된다.
