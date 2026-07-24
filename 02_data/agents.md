---
date: 2026-07-21
category: 스키마
data: agents
tags: [상담원, 상담품질]
source: "BigQuery `PROJECT1_DAY.agents01`"
---

## 개요

상담원(agent) 마스터 데이터. `raw/` 폴더에는 대응 파일이 없고, BigQuery `PROJECT1_DAY` 데이터셋의 `agents01` 테이블에서 직접 조회함. 20명, 20행.

**2026-07-23 정정**: 최초 작성 시(2026-07-21) source는 `project1_day1.agents`였으나, 실제로 다시 조회해보니 그 데이터셋(대문자 `PROJECT1_DAY1`)은 비어 있고 테이블은 `PROJECT1_DAY.agents01`로 위치가 바뀌어 있었음. 스키마(컬럼 구성·타입)와 `team`/`employment_type`/`training_completed_yn`/`turnover_yn`/`qa_score`의 분포는 최초 조회 시와 동일했지만, **`agent_satisfaction`·`overtime_hours_avg`는 개인별 값이 재시딩(reseed)되어 바뀌어 있었음** — 값의 범위(agent_satisfaction 2~9, overtime_hours_avg 4~28)는 같지만 어떤 agent_id가 어떤 값을 받았는지가 달라짐. 이로 인해 [[q-009-직원만족도-고객경험]]·[[i-004-직원만족도-고객경험]]의 eNPS·상관계수 결과가 갱신됨. 상세 이력은 두 노트 하단 참고.

## 컬럼

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| agent_id | STRING | 상담원 ID (PK). [[data_consultations]]의 `agent_id`와 연결되는 키 |
| team | STRING | 소속 팀. 값: 1팀(7명), 2팀(7명), 3팀(6명) |
| hire_date | DATE | 입사일. 2019-03-05 ~ 2024-06-01 범위 |
| employment_type | STRING | 고용 형태. 값: 정규직(16명), 계약직(4명) |
| monthly_call_target | INTEGER | 월 상담 목표 건수. 범위 60~90 |
| training_completed_yn | BOOLEAN | 교육 이수 여부. 20명 중 13명 이수(true) |
| qa_score | FLOAT | QA(품질관리) 점수. 범위 3.0~4.6, 평균 3.8. 만점 기준은 BigQuery 스키마에 설명이 없어 불명확 |
| overtime_hours_avg | INTEGER | 평균 초과근무 시간(월 기준으로 보임). 범위 4~28 |
| agent_satisfaction | INTEGER | 상담원(직원) 만족도 점수. 범위 2~9. 척도 기준(예: 10점 만점)은 불명확 |
| turnover_yn | BOOLEAN | 퇴사(이직) 여부. 20명 중 3명 true |

## 연결

- `agent_id` 기준으로 [[data_consultations]]와 연결된다. `data_consultations`에 등장하는 20개 `agent_id`(AG01~AG20)와 정확히 일치함을 확인함.
- [[data_consultations]] → [[data_satisfaction]](`consult_id`로 연결) 경로를 거치면 상담원별 CSAT·NPS와도 간접 연결할 수 있다.

## 비고

- `qa_score`, `agent_satisfaction`의 정확한 척도(만점 기준)는 BigQuery 컬럼 설명이 비어 있어 확인 불가. 값 범위로 미루어 짐작한 것이므로 정확한 정의는 추가 확인이 필요함 — 추측과 사실 구분.
- [[i-003-저만족도-채널요인]]에서 "상담원별 채널 배정 비율을 통제하지 않았다"는 한계를 지적한 바 있는데, 이 테이블의 `qa_score`·`overtime_hours_avg`·`turnover_yn` 등을 활용하면 agent_id 가설을 더 정교하게 검증할 수 있어 보임 — 후속 분석 후보.
