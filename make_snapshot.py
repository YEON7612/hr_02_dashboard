from google.cloud import bigquery
import pandas as pd

# 1. BigQuery 연결 (기존 내 컴퓨터 로그인 사용)
client = bigquery.Client()

# 2. 첫 번째 스냅샷 데이터 추출 및 CSV 저장 (agents)
agent_query = """
SELECT a.agent_id, a.team, a.overtime_hours_avg, a.agent_satisfaction, AVG(s.csat) AS avg_csat
FROM `PROJECT1_DAY.agents01` a
LEFT JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
LEFT JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
GROUP BY a.agent_id, a.team, a.overtime_hours_avg, a.agent_satisfaction
"""
df_agents = client.query(agent_query).to_dataframe()
df_agents.to_csv("data/agents_snapshot.csv", index=False, encoding="utf-8-sig")

# 3. 두 번째 스냅샷 데이터 추출 및 CSV 저장 (consultations)
consult_query = """
SELECT a.agent_id, a.team, a.training_completed_yn, c.is_recontact, s.csat
FROM `PROJECT1_DAY.agents01` a
JOIN `project1_day_03.consultations_table` c ON a.agent_id = c.agent_id
LEFT JOIN `project1_day_03.satisfaction_table` s ON c.consult_id = s.consult_id
"""
df_consults = client.query(consult_query).to_dataframe()
df_consults.to_csv("data/agent_consultations_snapshot.csv", index=False, encoding="utf-8-sig")

print("✅ 스냅샷 CSV 파일 생성 완료!")