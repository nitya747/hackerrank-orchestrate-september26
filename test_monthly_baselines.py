import pandas as pd

fe = pd.read_csv("dataset/financial_events.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")
sr = pd.read_csv("dataset/sample_requests.csv")

for idx, r in sr.iterrows():
    u_id = r['user_id']
    u_events = fe[fe['user_id'] == u_id].copy()
    u_events['dt'] = u_events['settlement_date'].fillna(u_events['event_date'])
    u_events = u_events[u_events['dt'] < r['request_date']]
    
    # Calculate monthly average debit by category
    debits = u_events[u_events['direction'] == 'debit']
    monthly_cat = debits.groupby('category')['amount'].sum() / 3.0 # approx 3 months history
    
    print(f"Sample {r['request_id']} ({u_id}): req_amt={r['requested_amount']}, safe_exp={r['amount_safe_to_pay']}")
    print("  Monthly avg debits by cat:")
    for cat, val in monthly_cat.items():
        if val > 0:
            print(f"    {cat:20s}: {val:10.2f}")
    print()
