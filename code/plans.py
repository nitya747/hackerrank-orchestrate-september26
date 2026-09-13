from datetime import datetime, timedelta

class CandidatePlan:
    def __init__(self, method, payments, spending_changes=None, option_id=None, total_cost=None):
        self.method = method                     # 'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'
        self.payments = payments                 # list of {'date': date_obj, 'amount': float}
        self.spending_changes = spending_changes or [] # list of str
        self.option_id = option_id or "999"      # for tie-breaking
        
        if total_cost is None:
            self.total_cost = sum(p['amount'] for p in payments)
        else:
            self.total_cost = float(total_cost)

    @property
    def start_date(self):
        if not self.payments:
            return datetime.max.date()
        return min(p['date'] for p in self.payments)

    @property
    def end_date(self):
        if not self.payments:
            return datetime.max.date()
        return max(p['date'] for p in self.payments)

    @property
    def num_payments(self):
        return len(self.payments)

    def format_plan_string(self):
        if not self.payments or self.method == 'not_recommended':
            return 'none'
        # Sort payments chronologically
        sorted_pmts = sorted(self.payments, key=lambda x: x['date'])
        parts = []
        for p in sorted_pmts:
            dt_str = p['date'].strftime("%Y-%m-%d")
            # Format amount cleanly
            amt = p['amount']
            if amt == int(amt):
                amt_str = f"{int(amt)}"
            else:
                amt_str = f"{amt:.2f}".rstrip('0').rstrip('.')
            parts.append(f"{dt_str}:{amt_str}")
        return "|".join(parts)

    def format_spending_changes(self):
        if not self.spending_changes:
            return 'none'
        return "|".join(self.spending_changes)
