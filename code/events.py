from datetime import datetime, timedelta, date
import pandas as pd

FIXED_COMMITMENT_CATS = {
    'rent', 'housing', 'utilities', 'debt_repayment', 'education', 
    'insurance', 'healthcare', 'salary', 'cloud_storage', 'streaming', 
    'music_subscription', 'delivery_membership', 'gym', 'family_support', 'transport'
}

class EventManager:
    def __init__(self, loader, evidence):
        self.loader = loader
        self.evidence = evidence

    def get_user_events(self, user_id, request_date_str):
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        profile = self.loader.get_user_profile(user_id)
        home_curr = profile['home_currency']
        
        raw_events = self.loader.events_df[self.loader.events_df['user_id'] == user_id].copy()
        
        processed_events = []
        linked_to_ignore = set()

        for _, row in raw_events.iterrows():
            if pd.notna(row['linked_event_id']):
                linked_to_ignore.add(str(row['linked_event_id']))

        user_facts = self.evidence.get_user_facts(user_id)

        for _, row in raw_events.iterrows():
            event_id = str(row['event_id'])
            status = str(row['status']).strip()

            if status in ['failed', 'cancelled'] or event_id in linked_to_ignore:
                continue
            
            amount = row['amount']
            if pd.isna(amount):
                img_rows = self.loader.images_df[self.loader.images_df['related_event_id'] == event_id]
                if not img_rows.empty:
                    image_id = img_rows.iloc[0]['image_id']
                    amount = self.evidence.get_image_amount(image_id)
            
            if amount is None or pd.isna(amount):
                continue
            
            amount = float(amount)
            event_curr = str(row['currency']).strip()

            dt_str = str(row['settlement_date']).split('T')[0] if pd.notna(row['settlement_date']) else str(row['event_date']).split('T')[0]
            event_dt = datetime.strptime(dt_str, "%Y-%m-%d").date()

            home_amount = self.loader.convert_currency(amount, event_curr, home_curr, dt_str)

            evt = {
                'event_id': event_id,
                'user_id': user_id,
                'event_type': str(row['event_type']),
                'description': str(row['description']),
                'category': str(row['category']),
                'direction': str(row['direction']),
                'original_amount': amount,
                'original_currency': event_curr,
                'amount': home_amount,
                'currency': home_curr,
                'date': event_dt,
                'date_str': dt_str,
                'status': status,
                'flexibility': str(row['flexibility']),
                'minimum_allowed_amount': float(row['minimum_allowed_amount']) if pd.notna(row.get('minimum_allowed_amount')) else None
            }
            processed_events.append(evt)

        return processed_events, user_facts

    def project_90day_cashflow(self, user_id, request_date_str, processed_events, user_facts):
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        end_dt = req_dt + timedelta(days=90)
        profile = self.loader.get_user_profile(user_id)
        home_curr = profile['home_currency']

        future_cashflows = []
        
        updated_salary_amount = None
        updated_salary_date_day = None
        for fact in user_facts:
            if fact['type'] == 'salary_amount_change':
                sal_amt = fact['salary_amount']
                sal_curr = fact.get('salary_currency', home_curr) or home_curr
                updated_salary_amount = self.loader.convert_currency(sal_amt, sal_curr, home_curr, request_date_str)
            elif fact['type'] == 'salary_date_change':
                updated_salary_date_day = int(fact['new_date'].split('-')[2])

        hist_events = [e for e in processed_events if e['date'] < req_dt and e['status'] == 'settled']
        known_future = [e for e in processed_events if e['date'] >= req_dt]

        for e in known_future:
            if e['status'] == 'pending' and e['direction'] != 'debit':
                continue
            if e['direction'] == 'non_cash':
                continue
            
            if e['category'] == 'salary' and updated_salary_amount is not None:
                e['amount'] = updated_salary_amount

            future_cashflows.append(e)

        # Project fixed recurring monthly commitments from past 35 days
        recent_hist = [e for e in hist_events if req_dt - timedelta(days=35) <= e['date'] < req_dt]
        
        for h in recent_hist:
            cat = h['category']
            if cat not in FIXED_COMMITMENT_CATS:
                continue
                
            h_dt = h['date']
            target_day = updated_salary_date_day if (cat == 'salary' and updated_salary_date_day) else h_dt.day
            amt = updated_salary_amount if (cat == 'salary' and updated_salary_amount) else h['amount']
            
            curr_y, curr_m = req_dt.year, req_dt.month
            for offset in range(4):
                m = (curr_m + offset - 1) % 12 + 1
                y = curr_y + (curr_m + offset - 1) // 12
                try:
                    p_dt = date(y, m, min(target_day, 28))
                except ValueError:
                    p_dt = date(y, m, 28)
                    
                if req_dt <= p_dt <= end_dt:
                    already = any(k['category'] == cat and abs((k['date'] - p_dt).days) <= 3 for k in known_future)
                    if not already:
                        future_cashflows.append({
                            'event_id': h['event_id'], # preserve original event_id for spending_changes matching!
                            'user_id': user_id,
                            'event_type': h['event_type'],
                            'description': f"Projected {h['description']}",
                            'category': cat,
                            'direction': h['direction'],
                            'original_amount': amt,
                            'original_currency': home_curr,
                            'amount': amt,
                            'currency': home_curr,
                            'date': p_dt,
                            'date_str': p_dt.strftime("%Y-%m-%d"),
                            'status': 'scheduled',
                            'flexibility': h['flexibility'],
                            'minimum_allowed_amount': h['minimum_allowed_amount']
                        })

        future_cashflows.sort(key=lambda x: x['date'])
        return future_cashflows
