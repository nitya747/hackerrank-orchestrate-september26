import os
import sys
import pandas as pd
from datetime import datetime

ALLOWED_STATUSES = {'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'}
ALLOWED_METHODS = {'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'}
REQUIRED_COLUMNS = [
    'request_id',
    'amount_safe_to_pay',
    'affordability_status',
    'recommended_payment_method',
    'payment_plan',
    'earliest_date_for_full_payment',
    'spending_changes_needed',
    'decision_explanation'
]

def validate_output(output_file="output.csv", dataset_dir="dataset"):
    if not os.path.exists(output_file):
        print(f"ERROR: Output file '{output_file}' does not exist.")
        return False

    out_df = pd.read_csv(output_file)
    requests_df = pd.read_csv(os.path.join(dataset_dir, "requests.csv"))

    errors = []

    # 1. Column Order & Names
    if list(out_df.columns) != REQUIRED_COLUMNS:
        errors.append(f"Column mismatch. Got {list(out_df.columns)}, expected {REQUIRED_COLUMNS}")

    # 2. Row Count & Request IDs
    req_ids_expected = list(requests_df['request_id'])
    req_ids_actual = list(out_df['request_id'])

    if len(req_ids_actual) != len(req_ids_expected):
        errors.append(f"Row count mismatch. Expected {len(req_ids_expected)}, got {len(req_ids_actual)}")

    if set(req_ids_actual) != set(req_ids_expected):
        missing = set(req_ids_expected) - set(req_ids_actual)
        extra = set(req_ids_actual) - set(req_ids_expected)
        errors.append(f"Request ID set mismatch. Missing: {missing}, Extra: {extra}")

    if len(req_ids_actual) != len(set(req_ids_actual)):
        errors.append("Duplicate request_ids found in output.")

    # 3. Row-by-row Validation
    req_lookup = requests_df.set_index('request_id').to_dict(orient='index')

    for idx, row in out_df.iterrows():
        r_id = row['request_id']
        if r_id not in req_lookup:
            continue
        req_meta = req_lookup[r_id]

        req_date = str(req_meta['request_date']).split('T')[0]
        desired_date = str(req_meta['desired_completion_date']).split('T')[0]
        requested_amt = float(req_meta['requested_amount'])
        allows_partial = str(req_meta['allows_partial_payment']).strip().lower() in ['true', '1', 'yes']

        safe_amt = float(row['amount_safe_to_pay'])
        status = str(row['affordability_status']).strip()
        method = str(row['recommended_payment_method']).strip()
        plan_str = str(row['payment_plan']).strip()
        earliest_date = str(row['earliest_date_for_full_payment']).strip() if pd.notna(row['earliest_date_for_full_payment']) else ""
        spending_changes = str(row['spending_changes_needed']).strip()
        explanation = str(row['decision_explanation']).strip()

        # Enums
        if status not in ALLOWED_STATUSES:
            errors.append(f"Row {r_id}: Invalid affordability_status '{status}'")
        if method not in ALLOWED_METHODS:
            errors.append(f"Row {r_id}: Invalid recommended_payment_method '{method}'")

        # Range for safe_amt
        if not (0 <= safe_amt <= requested_amt + 1e-4):
            errors.append(f"Row {r_id}: amount_safe_to_pay {safe_amt} out of bounds [0, {requested_amt}]")

        # affordable_now invariant
        if status == 'affordable_now':
            if earliest_date != req_date:
                errors.append(f"Row {r_id}: status is 'affordable_now' but earliest_date '{earliest_date}' != request_date '{req_date}'")

        # partial_payment invariant
        if method == 'partial_payment':
            if not allows_partial:
                errors.append(f"Row {r_id}: recommended partial_payment but request does not allow partial payment")
            if not (0 < safe_amt < requested_amt):
                errors.append(f"Row {r_id}: recommended partial_payment but safe_amt {safe_amt} is not strictly between 0 and {requested_amt}")
            
            # Parse plan
            parts = plan_str.split('|')
            if len(parts) != 2:
                errors.append(f"Row {r_id}: partial_payment plan must have exactly 2 payments, got '{plan_str}'")
            else:
                p1_dt, p1_amt = parts[0].split(':')
                p2_dt, p2_amt = parts[1].split(':')
                tot = float(p1_amt) + float(p2_amt)
                if abs(tot - requested_amt) > 1.0:
                    errors.append(f"Row {r_id}: partial_payment sum {tot} != requested_amount {requested_amt}")
                if p2_dt != earliest_date:
                    errors.append(f"Row {r_id}: partial_payment second date '{p2_dt}' != earliest_date '{earliest_date}'")
                if p2_dt > desired_date:
                    errors.append(f"Row {r_id}: partial_payment second date '{p2_dt}' > desired_completion_date '{desired_date}'")

        # Spending changes limits
        if spending_changes != 'none':
            sc_list = spending_changes.split('|')
            if len(sc_list) > 3:
                errors.append(f"Row {r_id}: >3 spending changes specified '{spending_changes}'")
            
            events_modified = [s.split(':')[1] for s in sc_list]
            if len(events_modified) != len(set(events_modified)):
                errors.append(f"Row {r_id}: duplicate event modified in spending_changes '{spending_changes}'")

        # Explanation presence
        if not explanation or len(explanation) < 10:
            errors.append(f"Row {r_id}: decision_explanation is missing or too short")

    if errors:
        print(f"=== VALIDATION FAILED WITH {len(errors)} ERRORS ===")
        for e in errors[:20]:
            print(f"  - {e}")
        return False
    else:
        print(f"=== OUTPUT VALIDATION PASSED PERFECTLY ({len(out_df)} rows) ===")
        return True

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "output.csv"
    validate_output(out_file)
