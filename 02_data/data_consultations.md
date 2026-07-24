---
date: 2026-07-10
category: 스키마
data: data_consultations
tags: [상담로그]
source: "[[raw/data_consultations.csv]]"
---

## 개요

상담 로그 데이터. 1,320건, 1321행(헤더 포함).

## 컬럼

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| consult_id | string | 상담 ID (PK). [[data_satisfaction]]과 연결되는 키 |
| customer_id | string | 고객 ID (FK) |
| consult_date | date | 상담일 |
| channel | string | 상담 채널. 값: 전화, 앱, 채팅, 이메일 |
| category | string | 상담 카테고리. 값: 해지문의, 장애신고, 요금문의, 부가서비스, 명의변경, 기타 |
| duration_min | int | 상담 소요 시간(분) |
| status | string | 처리 상태. 값: 완료, 미해결, 재문의 |
| is_recontact | string | 재문의 여부. 값: Y, N |
| agent_id | string | 상담원 ID. [[agents]]의 `agent_id`와 연결되는 키 |

## 연결

- `customer_id` 기준으로 [[data_customers]]와 연결된다.
- `consult_id` 기준으로 [[data_satisfaction]]과 연결된다.
- `agent_id` 기준으로 [[agents]](BigQuery `PROJECT1_DAY.agents01`)와 연결된다.

## 참고

- `status`(재문의)와 `is_recontact` 컬럼으로 재문의율을 계산할 수 있음. 재문의율 20% 이상이면 개선 필요로 판단하는 기준([[CLAUDE]] 참고)과 연결해 분석 가능.
