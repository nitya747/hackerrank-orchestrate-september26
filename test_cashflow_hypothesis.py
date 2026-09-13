import pandas as pd
from datetime import datetime, timedelta, date

from code.loader import DataLoader
from code.evidence import EvidenceExtractor
from code.events import EventManager
from code.planner import FinancialPlanner

loader = DataLoader()
evidence = EvidenceExtractor(loader)
event_manager = EventManager(loader, evidence)
planner = FinancialPlanner(loader, event_manager)

samples_df = loader.sample_requests_df

print("=== TESTING EXACT CASHFLOW HYPOTHESIS ON SAMPLES ===")

for idx, row in samples_df.iterrows():
    req_id = row['request_id']
    user_id = row['user_id']
    req_dt_str = str(row['request_date']).split('T')[0]
    req_dt = datetime.strptime(req_dt_str, "%Y-%m-%d").date()
    
    events, user_facts = event_manager.get_user_events(user_id, req_dt_str)
    
    # Simple future cashflows: known events >= req_dt
    known_future = [e for e in events if e['date'] >= req_dt]
    
    # Check if salary is present in future
    has_future_salary = any(e['category'] == 'salary' for e in known_future)
    
    if not has_future_salary:
        # Find past salary to get day of month & amount
        past_salaries = [e for e in events if e['date'] < req_dt and e['category'] == 'salary' and e['status'] == 'settled']
        if past_salaries:
            past_salaries.sort(key=lambda x: x['date'])
            last_sal = past_salaries[-1]
            sal_day = last_sal['date'].day
            sal_amt = last_sal['amount']
            
            # Project salary for next 3 months
            curr_y, curr_m = req_dt.year, req_dt.month
            for offset in range(3):
                m = (curr_m + offset - 1) % 12 + 1
                y = curr_y + (curr_m + offset - 1) // 12
                try:
                    s_dt = date(y, m, min(sal_day, 28))
                except ValueError:
                    s_dt = date(y, m, 28)
                    
                if req_dt <= s_dt <= req_dt + timedelta(days=90):
                    known_future.append({
                        'event_id': f"proj_sal_{s_dt.strftime('%Y%m%d')}",
                        'user_id': user_id,
                        'event_type': 'income',
                        'description': 'Projected Salary',
                        'category': 'salary',
                        'direction': 'credit',
                        'amount': sal_amt,
                        'currency': last_sal['currency'],
                        'date': s_dt,
                        'date_str': s_dt.strftime("%Y-%m-%d"),
                        'status': 'scheduled',
                        'flexibility': 'fixed'
                    })
                    
    known_future.sort(key=lambda x: x['date'])
    
    # Compute safe_amt with this clean cashflow
    from code.forecast import DailySimulator
    profile = loader.get_user_profile(user_id)
    sim = DailySimulator(profile, known_future, req_dt_str, forecast_days=90)
    
    requested_amount = float(row['requested_amount'])
    safe_amt = planner.compute_amount_safe_to_pay(sim, requested_amount, req_dt)
    earliest_dt = planner.compute_earliest_date_for_full_payment(sim, requested_amount, req_dt)
    
    exp_safe = float(row['amount_safe_to_pay'])
    exp_earliest = str(row['earliest_date_for_full_payment']).strip() if pd.notna(row['earliest_date_for_full_payment']) else ""
    pred_earliest = earliest_dt.strftime("%Y-%m-%d") if earliest_dt else ""
    
    diff = abs(safe_amt - exp_safe)
    match_tag = "MATCH" if diff < 1.0 else f"DIFF: {diff:.2f}"
    print(f"Sample {req_id:12s} ({user_id}): P_safe={safe_amt:12.2f} | E_safe={exp_safe:12.2f} | Tag={match_tag:12s} | P_earliest={pred_earliest:10s} | E_earliest={exp_earliest:10s}")
