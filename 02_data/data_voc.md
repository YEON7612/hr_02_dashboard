---
date: 2026-07-10
category: 스키마
data: data_voc
tags: [VOC]
source: "[[raw/data_voc.csv]]"
---

## 개요

VOC(고객의 소리) 데이터. 1,307건, 1308행(헤더 포함).

## 컬럼

| 컬럼명           | 타입     | 설명                                  |
| ------------- | ------ | ----------------------------------- |
| voc_id        | string | VOC ID (PK)                         |
| customer_id   | string | 고객 ID (FK)                          |
| received_date | date   | 접수일. 2024-01 ~ 2024-12 범위로 보임       |
| channel       | string | 접수 채널. 값: 앱리뷰, 고객센터전화, SNS, 이메일     |
| voc_type      | string | VOC 유형. 값: 문의, 불만, 제안, 칭찬           |
| category      | string | 카테고리. 값: 품질, 요금, 서비스, 앱기능, 해지관련, 기타 |
| content       | string | VOC 내용(자유 텍스트)                      |
| sentiment     | string | 감성. 값: 긍정, 중립, 부정                   |

## 연결

- `customer_id` 기준으로 [[data_customers]]와 연결된다.
