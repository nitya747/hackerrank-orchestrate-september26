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

def run_pipeline(dataset_dir="dataset", output_file="output.csv"):
    print(f"Loading data from '{dataset_dir}'...")
    loader = DataLoader(dataset_dir=dataset_dir)
    evidence = EvidenceExtractor(loader)
    event_manager = EventManager(loader, evidence)
    planner = FinancialPlanner(loader, event_manager)
    output_gen = OutputGenerator(loader)

    requests_df = loader.requests_df
    results = []

    print(f"Evaluating {len(requests_df)} requests...")
    for idx, row in requests_df.iterrows():
        eval_res = planner.evaluate_request(row)
        explanation = output_gen.generate_explanation(eval_res, row)

        out_row = {
            'request_id': eval_res['request_id'],
            'amount_safe_to_pay': eval_res['amount_safe_to_pay'],
            'affordability_status': eval_res['affordability_status'],
            'recommended_payment_method': eval_res['recommended_payment_method'],
            'payment_plan': eval_res['payment_plan'],
            'earliest_date_for_full_payment': eval_res['earliest_date_for_full_payment'],
            'spending_changes_needed': eval_res['spending_changes_needed'],
            'decision_explanation': explanation
        }
        results.append(out_row)

    out_df = pd.DataFrame(results)
    cols = [
        'request_id',
        'amount_safe_to_pay',
        'affordability_status',
        'recommended_payment_method',
        'payment_plan',
        'earliest_date_for_full_payment',
        'spending_changes_needed',
        'decision_explanation'
    ]
    out_df = out_df[cols]
    out_df.to_csv(output_file, index=False)
    print(f"Successfully generated '{output_file}' with {len(out_df)} rows.")

if __name__ == "__main__":
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "dataset"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "output.csv"
    run_pipeline(dataset_dir=dataset_path, output_file=out_path)
