import pandas as pd

er = pd.read_csv("dataset/exchange_rates.csv")
fe = pd.read_csv("dataset/financial_events.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")

fe_user = fe.merge(fp[["user_id", "home_currency"]], on="user_id")
diff_curr = fe_user[fe_user["currency"] != fe_user["home_currency"]].copy()

rate_map = {}
for _, r in er.iterrows():
    d, f, t, rate = str(r['rate_date']), str(r['from_currency']), str(r['to_currency']), float(r['rate'])
    rate_map[(d, f, t)] = rate
    rate_map[(d, t, f)] = 1.0 / rate

missing_count = 0
for _, r in diff_curr.iterrows():
    dt = str(r['settlement_date']) if pd.notna(r['settlement_date']) else str(r['event_date'])
    fc, tc = str(r['currency']), str(r['home_currency'])
    if (dt, fc, tc) not in rate_map:
        missing_count += 1
        avail = [d for (d, f, t) in rate_map.keys() if f == fc and t == tc]
        if missing_count <= 10:
            print(f"Missing exact rate for event {r['event_id']}: date={dt}, {fc}->{tc}. Available dates count: {len(avail)}")

print(f"Total missing exact rate lookups: {missing_count} / {len(diff_curr)}")
