from datetime import datetime, timedelta

class SimulationResult:
    def __init__(self, is_safe, min_balance, min_balance_date, final_balance, violations):
        self.is_safe = is_safe
        self.min_balance = min_balance
        self.min_balance_date = min_balance_date
        self.final_balance = final_balance
        self.violations = violations

class DailySimulator:
    def __init__(self, user_profile, future_cashflows, request_date_str, forecast_days=90):
        self.user_profile = user_profile
        self.future_cashflows = future_cashflows
        self.request_date = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        self.forecast_days = forecast_days
        self.end_date = self.request_date + timedelta(days=forecast_days)
        self.minimum_balance = float(user_profile['minimum_balance_to_keep'])
        self.starting_balance = float(user_profile['current_available_balance'])

    def simulate(self, candidate_payments=None, spending_changes=None):
        if candidate_payments is None:
            candidate_payments = []
        if spending_changes is None:
            spending_changes = []

        # Parse spending changes into lookup maps
        stopped_events = set()
        reduced_events = {}
        for change in spending_changes:
            parts = change.split(':')
            if parts[0] == 'stop':
                stopped_events.add(parts[1])
            elif parts[0] == 'reduce_to':
                reduced_events[parts[1]] = float(parts[2])

        # Group candidate payments by date
        pmts_by_date = {}
        for pmt in candidate_payments:
            p_dt = pmt['date']
            if p_dt not in pmts_by_date:
                pmts_by_date[p_dt] = 0.0
            pmts_by_date[p_dt] += float(pmt['amount'])

        # Group future cashflows by date
        cf_by_date = {}
        for cf in self.future_cashflows:
            c_dt = cf['date']
            if c_dt not in cf_by_date:
                cf_by_date[c_dt] = []
            cf_by_date[c_dt].append(cf)

        current_balance = self.starting_balance
        min_balance = current_balance
        min_balance_date = self.request_date
        violations = []

        curr_dt = self.request_date
        while curr_dt <= self.end_date:
            # 1. Apply candidate plan payments on curr_dt
            if curr_dt in pmts_by_date:
                current_balance -= pmts_by_date[curr_dt]

            # 2. Apply scheduled cashflows on curr_dt
            if curr_dt in cf_by_date:
                for cf in cf_by_date[curr_dt]:
                    evt_id = cf['event_id']
                    
                    # Check spending changes
                    if evt_id in stopped_events:
                        continue
                    
                    amt = cf['amount']
                    if evt_id in reduced_events:
                        amt = min(amt, reduced_events[evt_id])
                    
                    if cf['direction'] == 'debit':
                        current_balance -= amt
                    elif cf['direction'] == 'credit':
                        current_balance += amt

            # Check min balance
            if current_balance < min_balance:
                min_balance = current_balance
                min_balance_date = curr_dt

            if current_balance < self.minimum_balance:
                violations.append((curr_dt, current_balance))

            curr_dt += timedelta(days=1)

        is_safe = (len(violations) == 0) and (min_balance >= self.minimum_balance)
        return SimulationResult(is_safe, min_balance, min_balance_date, current_balance, violations)
