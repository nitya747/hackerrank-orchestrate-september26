import os
import sys
import pandas as pd

# Add repo root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.loader import DataLoader
from code.evidence import EvidenceExtractor
from code.events import EventManager
from code.planner import FinancialPlanner
from code.output import OutputGenerator

def evaluate_samples(dataset_dir="dataset"):
    loader = DataLoader(dataset_dir=dataset_dir)
    evidence = EvidenceExtractor(loader)
    event_manager = EventManager(loader, evidence)
    planner = FinancialPlanner(loader, event_manager)
    output_gen = OutputGenerator(loader)

    samples_df = loader.sample_requests_df
    if samples_df is None or samples_df.empty:
        print("No sample_requests.csv found.")
        return

    print(f"=== EVALUATING {len(samples_df)} SAMPLE REQUESTS ===")

    metrics = {
        'amount_safe_to_pay': 0,
        'affordability_status': 0,
        'recommended_payment_method': 0,
        'payment_plan': 0,
        'earliest_date_for_full_payment': 0,
        'spending_changes_needed': 0,
        'total': len(samples_df)
    }

    mismatches = []

    for idx, row in samples_df.iterrows():
        eval_res = planner.evaluate_request(row)
        explanation = output_gen.generate_explanation(eval_res, row)

        pred_safe_amt = eval_res['amount_safe_to_pay']
        pred_status = eval_res['affordability_status']
        pred_method = eval_res['recommended_payment_method']
        pred_plan = eval_res['payment_plan']
        pred_earliest = eval_res['earliest_date_for_full_payment']
        pred_changes = eval_res['spending_changes_needed']

        exp_safe_amt = float(row['amount_safe_to_pay'])
        exp_status = str(row['affordability_status']).strip()
        exp_method = str(row['recommended_payment_method']).strip()
        exp_plan = str(row['payment_plan']).strip()
        exp_earliest = str(row['earliest_date_for_full_payment']).strip() if pd.notna(row['earliest_date_for_full_payment']) else ""
        exp_changes = str(row['spending_changes_needed']).strip()

        # Check field matches
        match_safe = abs(pred_safe_amt - exp_safe_amt) < 1.0
        match_status = (pred_status == exp_status)
        match_method = (pred_method == exp_method)
        match_plan = (pred_plan == exp_plan)
        match_earliest = (pred_earliest == exp_earliest)
        match_changes = (pred_changes == exp_changes)

        if match_safe: metrics['amount_safe_to_pay'] += 1
        if match_status: metrics['affordability_status'] += 1
        if match_method: metrics['recommended_payment_method'] += 1
        if match_plan: metrics['payment_plan'] += 1
        if match_earliest: metrics['earliest_date_for_full_payment'] += 1
        if match_changes: metrics['spending_changes_needed'] += 1

        if not (match_safe and match_status and match_method and match_plan and match_earliest and match_changes):
            mismatches.append({
                'request_id': row['request_id'],
                'safe_amt': (pred_safe_amt, exp_safe_amt),
                'status': (pred_status, exp_status),
                'method': (pred_method, exp_method),
                'plan': (pred_plan, exp_plan),
                'earliest': (pred_earliest, exp_earliest),
                'changes': (pred_changes, exp_changes)
            })

    print(f"\n--- ACCURACY METRICS ({metrics['total']} samples) ---")
    for key, val in metrics.items():
        if key != 'total':
            pct = (val / metrics['total']) * 100.0
            print(f"  {key:30s}: {val:2d}/{metrics['total']} ({pct:5.1f}%)")

    if mismatches:
        print(f"\n--- MISMATCHES DETAILED ({len(mismatches)}) ---")
        for m in mismatches:
            print(f"Request {m['request_id']}:")
            print(f"  safe_amt : P={m['safe_amt'][0]} | E={m['safe_amt'][1]}")
            print(f"  status   : P={m['status'][0]} | E={m['status'][1]}")
            print(f"  method   : P={m['method'][0]} | E={m['method'][1]}")
            print(f"  plan     : P={m['plan'][0]} | E={m['plan'][1]}")
            print(f"  earliest : P={m['earliest'][0]} | E={m['earliest'][1]}")
            print(f"  changes  : P={m['changes'][0]} | E={m['changes'][1]}")

if __name__ == "__main__":
    evaluate_samples()
