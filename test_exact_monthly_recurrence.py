import pandas as pd
from datetime import datetime, timedelta, date

from code.loader import DataLoader
from code.evidence import EvidenceExtractor
from code.events import EventManager
from code.planner import FinancialPlanner
from code.forecast import DailySimulator

loader = DataLoader()
evidence = EvidenceExtractor(loader)

samples_df = loader.sample_requests_df

for idx, row in samples_df.iterrows():
    req_id = row['request_id']
    user_id = row['user_id']
    req_dt_str = str(row['request_date']).split('T')[0]
    req_dt = datetime.strptime(req_dt_str, "%Y-%m-%d").date()
    end_dt = req_dt + timedelta(days=90)
    
    profile = loader.get_user_profile(user_id)
    home_curr = profile['home_currency']
    
    # Get raw user events
    u_events = loader.events_df[loader.events_df['user_id'] == user_id].copy()
    
    # Process valid events
    valid_events = []
    linked_to_ignore = set()
    for _, r in u_events.iterrows():
        if pd.notna(r['linked_event_id']):
            linked_to_ignore.add(str(r['linked_event_id']))
            
    for _, r in u_events.iterrows():
        evt_id = str(r['event_id'])
        status = str(r['status']).strip()
        if status in ['failed', 'cancelled'] or evt_id in linked_to_ignore:
            continue
            
        amt = r['amount']
        if pd.isna(amt):
            img_rows = loader.images_df[loader.images_df['related_event_id'] == evt_id]
            if not img_rows.empty:
                amt = evidence.get_image_amount(img_rows.iloc[0]['image_id'])
                
        if amt is None or pd.isna(amt):
            continue
            
        amt = float(amt)
        dt_str = str(r['settlement_date']).split('T')[0] if pd.notna(r['settlement_date']) else str(r['event_date']).split('T')[0]
        evt_dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
        home_amt = loader.convert_currency(amt, r['currency'], home_curr, dt_str)
        
        valid_events.append({
            'event_id': evt_id,
            'user_id': user_id,
            'category': str(r['category']),
            'direction': str(r['direction']),
            'amount': home_amt,
            'date': evt_dt,
            'status': status,
            'flexibility': str(r['flexibility'])
        })
        
    # Build 90-day cashflow:
    # 1. Include future explicit events from dataset >= req_dt
    known_future = [e for e in valid_events if e['date'] >= req_dt]
    # Filter pending credits / non_cash
    known_future = [e for e in known_future if not (e['status'] == 'pending' and e['direction'] != 'debit') and e['direction'] != 'non_cash']
    
    # 2. Find all distinct recurring monthly events in the 30 days prior to req_dt
    hist_events = [e for e in valid_events if req_dt - timedelta(days=35) <= e['date'] < req_dt and e['status'] == 'settled']
    
    # Group by category and description/amount
    for h in hist_events:
        cat = h['category']
        h_dt = h['date']
        target_day = h_dt.day
        
        # Project for next 3 months
        curr_y, curr_m = req_dt.year, req_dt.month
        for offset in range(4):
            m = (curr_m + offset - 1) % 12 + 1
            y = curr_y + (curr_m + offset - 1) // 12
            try:
                p_dt = date(y, m, min(target_day, 28))
            except ValueError:
                p_dt = date(y, m, 28)
                
            if req_dt <= p_dt <= end_dt:
                # Avoid duplicating if explicit event is already present near this date
                already = any(k['category'] == cat and abs((k['date'] - p_dt).days) <= 3 for k in known_future)
                if not already:
                    known_future.append({
                        'event_id': f"proj_{cat}_{p_dt.strftime('%Y%m%d')}",
                        'user_id': user_id,
                        'category': cat,
                        'direction': h['direction'],
                        'amount': h['amount'],
                        'date': p_dt,
                        'status': 'scheduled',
                        'flexibility': h['flexibility']
                    })
                    
    known_future.sort(key=lambda x: x['date'])
    
    sim = DailySimulator(profile, known_future, req_dt_str, forecast_days=90)
    planner = FinancialPlanner(loader, EventManager(loader, evidence))
    
    req_amt = float(row['requested_amount'])
    safe_amt = planner.compute_amount_safe_to_pay(sim, req_amt, req_dt)
    earliest_dt = planner.compute_earliest_date_for_full_payment(sim, req_amt, req_dt)
    
    exp_safe = float(row['amount_safe_to_pay'])
    exp_earliest = str(row['earliest_date_for_full_payment']).strip() if pd.notna(row['earliest_date_for_full_payment']) else ""
    pred_earliest = earliest_dt.strftime("%Y-%m-%d") if earliest_dt else ""
    
    diff = abs(safe_amt - exp_safe)
    match_tag = "EXACT MATCH" if diff < 1.0 else f"DIFF: {diff:.2f}"
    print(f"Sample {req_id:12s}: P_safe={safe_amt:12.2f} | E_safe={exp_safe:12.2f} | {match_tag:15s} | P_earliest={pred_earliest:10s} | E_earliest={exp_earliest:10s}")
