import pandas as pd

class OutputGenerator:
    def __init__(self, loader):
        self.loader = loader

    def format_currency(self, amt, currency):
        if amt is None:
            return f"{currency} 0"
        if amt == int(amt):
            amt_str = f"{int(amt):,}"
        else:
            amt_str = f"{amt:,.2f}".rstrip('0').rstrip('.')
        return f"{currency} {amt_str}"

    def generate_explanation(self, eval_result, request_row):
        user_id = request_row['user_id']
        req_amt = float(request_row['requested_amount'])
        desired_date = str(request_row['desired_completion_date']).split('T')[0]
        profile = self.loader.get_user_profile(user_id)
        curr = profile['home_currency']
        min_bal = float(profile['minimum_balance_to_keep'])
        
        safe_amt = eval_result['amount_safe_to_pay']
        status = eval_result['affordability_status']
        method = eval_result['recommended_payment_method']
        plan = eval_result['best_plan']
        earliest_full = eval_result['earliest_date_for_full_payment']
        spending_changes = eval_result['spending_changes_needed']

        curr_fmt = self.format_currency(req_amt, curr)
        min_fmt = self.format_currency(min_bal, curr)

        if method == 'full_payment' and status == 'affordable_now':
            return f"Pay {curr_fmt} today. This preserves the required minimum balance of {min_fmt} throughout the 90-day forecast."

        elif method == 'full_payment' and spending_changes != 'none':
            return f"With spending adjustments, pay {curr_fmt} today while preserving the required minimum balance of {min_fmt}."

        elif method == 'partial_payment':
            safe_fmt = self.format_currency(safe_amt, curr)
            rem_amt = req_amt - safe_amt
            rem_fmt = self.format_currency(rem_amt, curr)
            return f"Pay {safe_fmt} today and the remaining {rem_fmt} on {earliest_full}. This completes the full request by {desired_date} while protecting the {min_fmt} minimum balance."

        elif method == 'installments':
            num_pmts = plan.num_payments
            pmt_amt = plan.payments[0]['amount'] if plan.payments else 0.0
            pmt_fmt = self.format_currency(pmt_amt, curr)
            start_date = plan.start_date.strftime("%Y-%m-%d") if plan.payments else ""
            return f"Use {num_pmts} installments of {pmt_fmt}, starting {start_date}. This satisfies the request by {desired_date} while preserving the {min_fmt} minimum balance."

        elif method == 'wait':
            return f"Pay {curr_fmt} in full on {earliest_full}. Paying earlier would take the balance below the {min_fmt} minimum."

        else: # not_recommended
            if safe_amt > 0:
                safe_fmt = self.format_currency(safe_amt, curr)
                return f"Do not proceed with the {curr_fmt} request today. Although {safe_fmt} is available today, the full amount cannot be completed safely by {desired_date} while keeping the {min_fmt} minimum protected."
            else:
                return f"Do not make this payment by {desired_date}. None of the available options keeps the {min_fmt} minimum balance protected."
