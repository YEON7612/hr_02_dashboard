---
date: 2026-07-10
category: 스키마
data: data_satisfaction
tags: [만족도]
source: "[[raw/data_satisfaction.csv]]"
---

## 개요

만족도 설문 데이터. 1,320건, 1321행(헤더 포함). 상담 1건당 1건씩 연결되는 것으로 보임.

## 컬럼

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| satisfaction_id | string | 만족도 설문 ID (PK) |
| consult_id | string | 상담 ID (FK). [[data_consultations]]와 연결되는 키 |
| customer_id | string | 고객 ID (FK) |
| survey_date | date | 설문일 |
| csat | int | 고객만족도 점수. 범위 1~5 |
| nps | int | 순추천지수(NPS) 점수. 범위 0~10 |
| comment | string | 설문 코멘트(자유 텍스트). 비어있는 경우 있음 |

## 연결

- `consult_id` 기준으로 [[data_consultations]]와 연결된다. (다른 테이블과 달리 customer_id가 아닌 consult_id가 연결 키)
- `customer_id` 기준으로 [[data_customers]]와도 연결된다.
