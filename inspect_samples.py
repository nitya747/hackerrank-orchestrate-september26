import pandas as pd

sr = pd.read_csv("dataset/sample_requests.csv")
print(f"=== TOTAL SAMPLE REQUESTS: {len(sr)} ===")
for idx, r in sr.iterrows():
    print(f"--- SAMPLE {idx+1}: request_id={r['request_id']}, user_id={r['user_id']}, date={r['request_date']}, type={r['request_type']}, amt={r['requested_amount']}, desired_date={r['desired_completion_date']}, partial={r['allows_partial_payment']}")
    print(f"    Text: {r['request_text']}")
    print(f"    OUT: safe_amt={r['amount_safe_to_pay']}, status={r['affordability_status']}, method={r['recommended_payment_method']}, plan={r['payment_plan']}, earliest={r['earliest_date_for_full_payment']}, changes={r['spending_changes_needed']}")
    print(f"    Expl: {r['decision_explanation']}\n")
