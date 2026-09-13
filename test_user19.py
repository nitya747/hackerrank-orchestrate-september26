import pandas as pd

fe = pd.read_csv("dataset/financial_events.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")

u19_fp = fp[fp['user_id'] == 'user_19'].iloc[0]
u19_events = fe[fe['user_id'] == 'user_19'].sort_values('event_date')

print(f"User 19 profile: curr_bal={u19_fp['current_available_balance']}, min_bal={u19_fp['minimum_balance_to_keep']}")

print("\nRecent events for user_19:")
for _, r in u19_events.tail(30).iterrows():
    print(f"  {r['event_date']} | {r['event_id']} | {r['description']} | {r['category']} | {r['direction']} | {r['amount']} {r['currency']} | status={r['status']}")
