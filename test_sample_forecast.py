import pandas as pd
from datetime import datetime, timedelta

sr = pd.read_csv("dataset/sample_requests.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")
fe = pd.read_csv("dataset/financial_events.csv")

for idx, r in sr.iterrows():
    req_id = r['request_id']
    user_id = r['user_id']
    req_date = r['request_date']
    u_fp = fp[fp['user_id'] == user_id].iloc[0]
    
    # Get user events around request_date
    u_fe = fe[fe['user_id'] == user_id].copy()
    u_fe['dt'] = u_fe['settlement_date'].fillna(u_fe['event_date'])
    
    future_events = u_fe[u_fe['dt'] >= req_date].sort_values('dt')
    
    print(f"=== SAMPLE {req_id} ({user_id}, req_date={req_date}, curr_bal={u_fp['current_available_balance']}, min_bal={u_fp['minimum_balance_to_keep']}) ===")
    print(f"    Expected: safe_amt={r['amount_safe_to_pay']}, status={r['affordability_status']}, method={r['recommended_payment_method']}, plan={r['payment_plan']}")
    print(f"    Future events in CSV ({len(future_events)}):")
    for _, fe_row in future_events.head(10).iterrows():
        print(f"      {fe_row['dt']} | {fe_row['event_id']} | {fe_row['description']} | {fe_row['category']} | {fe_row['direction']} | {fe_row['amount']} {fe_row['currency']} | status={fe_row['status']}")
    print("\n")
