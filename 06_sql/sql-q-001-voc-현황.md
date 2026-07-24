---
date: 2026-07-14
category: SQL
data: "[[data_voc]]"
source_question: "[[q-001-voc-현황]]"
tags: [VOC, VOC분석, SQL]
---

[[q-001-voc-현황]]에 답하기 위한 빅쿼리(BigQuery Standard SQL) 쿼리. 테이블명은 `project.dataset.data_voc`로 표기했으니 실제 프로젝트/데이터셋명으로 바꿔서 사용한다.

## 1. voc_type별 건수와 비율

```sql
SELECT
  voc_type,
  COUNT(*) AS cnt,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM `project.dataset.data_voc`
GROUP BY voc_type
ORDER BY cnt DESC;
```

## 2. category별 전체건수·부정건수·부정비율

```sql
SELECT
  category,
  COUNT(*) AS total_cnt,
  COUNTIF(sentiment = '부정') AS negative_cnt,
  ROUND(SAFE_DIVIDE(COUNTIF(sentiment = '부정'), COUNT(*)) * 100, 1) AS negative_pct
FROM `project.dataset.data_voc`
GROUP BY category
ORDER BY negative_pct DESC;
```

## 3. 월별 전체건수·부정건수 추이

```sql
SELECT
  DATE_TRUNC(received_date, MONTH) AS year_month,
  COUNT(*) AS total_cnt,
  COUNTIF(sentiment = '부정') AS negative_cnt,
  ROUND(SAFE_DIVIDE(COUNTIF(sentiment = '부정'), COUNT(*)) * 100, 1) AS negative_pct
FROM `project.dataset.data_voc`
GROUP BY year_month
ORDER BY year_month;
```

## 기술 노트

- **`COUNTIF(조건)`** — BigQuery 전용 집계 함수. `SUM(CASE WHEN 조건 THEN 1 ELSE 0 END)`을 한 번에 대체한다.
- **`SAFE_DIVIDE(a, b)`** — `b = 0`이어도 에러 대신 `NULL`을 반환한다. group-by 비율 계산에는 습관적으로 쓰는 게 안전하다.
- **`SUM(COUNT(*)) OVER ()`** — GROUP BY로 집계된 결과에 빈 윈도우(`OVER ()`)를 붙이면 서브쿼리/self-join 없이 전체 총합을 각 행에 붙일 수 있다.
- **`DATE_TRUNC(date_col, MONTH)`** — `received_date`가 DATE 타입이라는 전제. 결과가 DATE 타입이라 정렬·차트 연동이 자연스럽다. 컬럼이 STRING으로 적재됐다면 `PARSE_DATE('%Y-%m-%d', received_date)`로 먼저 캐스팅해야 한다.
- **CSV 적재 시 BOM 주의**: `raw/` 원본 헤더 첫 컬럼 앞에 UTF-8 BOM(`﻿`)이 붙어 있다(예: `﻿voc_id,...`). `bq load` autodetect가 이를 잘 처리하는 버전도 있지만, 스키마 자동 감지 시 첫 컬럼명이 이상하게 잡히는 경우가 있으니 로드 후 `INFORMATION_SCHEMA.COLUMNS`로 실제 컬럼명을 확인하는 걸 권장한다.

## 관련 질문

- [[q-001-voc-현황]]
