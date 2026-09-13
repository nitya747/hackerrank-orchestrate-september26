import pandas as pd

fe = pd.read_csv("dataset/financial_events.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")
u2_fe = fe[fe['user_id'] == 'user_02'].sort_values('event_date')

print("=== USER_02 EVENTS ===")
for _, r in u2_fe.tail(25).iterrows():
    print(f"{r['event_date']} | {r['event_id']} | {r['description']} | {r['category']} | {r['direction']} | {r['amount']} {r['currency']} | status={r['status']} | flex={r['flexibility']}")
