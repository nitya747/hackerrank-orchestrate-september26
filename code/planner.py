import os
import sys
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forecast import DailySimulator
from plans import CandidatePlan

class FinancialPlanner:
    def __init__(self, loader, event_manager):
        self.loader = loader
        self.event_manager = event_manager

    def compute_amount_safe_to_pay(self, simulator, requested_amount, req_dt):
        low = 0.0
        high = float(requested_amount)
        best_safe = 0.0

        for _ in range(30):
            mid = (low + high) / 2.0
            res = simulator.simulate(candidate_payments=[{'date': req_dt, 'amount': mid}])
            if res.is_safe:
                best_safe = mid
                low = mid
            else:
                high = mid

        safe_amt = round(best_safe, 2)
        if safe_amt < 0.01:
            safe_amt = 0.0
        if safe_amt > requested_amount:
            safe_amt = float(requested_amount)
        return safe_amt

    def compute_earliest_date_for_full_payment(self, simulator, requested_amount, req_dt, max_days=90):
        curr_dt = req_dt
        end_dt = req_dt + timedelta(days=max_days)

        while curr_dt <= end_dt:
            res = simulator.simulate(candidate_payments=[{'date': curr_dt, 'amount': float(requested_amount)}])
            if res.is_safe:
                return curr_dt
            curr_dt += timedelta(days=1)

        return None

    def evaluate_request(self, request_row):
        req_id = request_row['request_id']
        user_id = request_row['user_id']
        req_dt_str = str(request_row['request_date']).split('T')[0]
        req_dt = datetime.strptime(req_dt_str, "%Y-%m-%d").date()
        requested_amount = float(request_row['requested_amount'])
        
        desired_comp_str = str(request_row['desired_completion_date']).split('T')[0]
        desired_comp_dt = datetime.strptime(desired_comp_str, "%Y-%m-%d").date()
        
        allows_partial = str(request_row['allows_partial_payment']).strip().lower() in ['true', '1', 'yes']

        profile = self.loader.get_user_profile(user_id)
        considered_methods = profile['payment_methods_user_will_consider']
        max_inst_months = profile['max_installment_months']

        events, user_facts = self.event_manager.get_user_events(user_id, req_dt_str)
        future_cashflows = self.event_manager.project_90day_cashflow(user_id, req_dt_str, events, user_facts)

        simulator = DailySimulator(profile, future_cashflows, req_dt_str, forecast_days=90)

        safe_amt = self.compute_amount_safe_to_pay(simulator, requested_amount, req_dt)
        earliest_full_dt = self.compute_earliest_date_for_full_payment(simulator, requested_amount, req_dt)

        candidates = []

        # Candidate A: Full Payment Today
        if 'full_payment' in considered_methods:
            res_full = simulator.simulate([{'date': req_dt, 'amount': requested_amount}])
            if res_full.is_safe:
                candidates.append(CandidatePlan(
                    method='full_payment',
                    payments=[{'date': req_dt, 'amount': requested_amount}],
                    spending_changes=[],
                    option_id='option_0_full',
                    total_cost=requested_amount
                ))

        # Candidate B: Partial Payment
        if allows_partial and ('partial_payment' in considered_methods):
            if 0 < safe_amt < requested_amount and earliest_full_dt is not None:
                if earliest_full_dt <= desired_comp_dt:
                    rem_amt = round(requested_amount - safe_amt, 2)
                    partial_pmts = [
                        {'date': req_dt, 'amount': safe_amt},
                        {'date': earliest_full_dt, 'amount': rem_amt}
                    ]
                    res_part = simulator.simulate(partial_pmts)
                    if res_part.is_safe:
                        candidates.append(CandidatePlan(
                            method='partial_payment',
                            payments=partial_pmts,
                            spending_changes=[],
                            option_id='option_0_partial',
                            total_cost=requested_amount
                        ))

        # Candidate C: Installments
        if 'installments' in considered_methods:
            opt_df = self.loader.payment_options_df[
                (self.loader.payment_options_df['request_id'] == req_id) &
                (self.loader.payment_options_df['payment_method'] == 'installments')
            ]
            for _, opt in opt_df.iterrows():
                opt_id = str(opt['payment_option_id'])
                pmt_amt = float(opt['payment_amount'])
                num_pmts = int(opt['number_of_payments'])
                first_date_str = str(opt['first_payment_date']).split('T')[0]
                first_dt = datetime.strptime(first_date_str, "%Y-%m-%d").date()
                freq_days = int(opt['payment_frequency_days']) if pd.notna(opt['payment_frequency_days']) else 30
                tot_payable = float(opt['total_payable_amount'])

                approx_months = (num_pmts * freq_days) / 30.0
                if max_inst_months is not None and approx_months > (max_inst_months + 0.5):
                    continue

                inst_pmts = []
                curr_p_dt = first_dt
                for p_idx in range(num_pmts):
                    inst_pmts.append({'date': curr_p_dt, 'amount': pmt_amt})
                    curr_p_dt = curr_p_dt + timedelta(days=freq_days)

                last_p_dt = inst_pmts[-1]['date']
                if last_p_dt <= desired_comp_dt:
                    res_inst = simulator.simulate(inst_pmts)
                    if res_inst.is_safe:
                        candidates.append(CandidatePlan(
                            method='installments',
                            payments=inst_pmts,
                            spending_changes=[],
                            option_id=opt_id,
                            total_cost=tot_payable
                        ))

        # Candidate D: Wait
        if ('full_payment' in considered_methods) and (earliest_full_dt is not None):
            if req_dt < earliest_full_dt <= desired_comp_dt:
                wait_pmts = [{'date': earliest_full_dt, 'amount': requested_amount}]
                res_wait = simulator.simulate(wait_pmts)
                if res_wait.is_safe:
                    candidates.append(CandidatePlan(
                        method='wait',
                        payments=wait_pmts,
                        spending_changes=[],
                        option_id='option_0_wait',
                        total_cost=requested_amount
                    ))

        # 3. If no baseline plan is available, evaluate permitted spending changes
        if not candidates:
            spending_candidates = self._generate_spending_change_plans(
                profile, future_cashflows, req_dt, requested_amount, desired_comp_dt, simulator, considered_methods
            )
            candidates.extend(spending_candidates)

        # 4. Select best plan or fallback to not_recommended
        if not candidates:
            best_plan = CandidatePlan(
                method='not_recommended',
                payments=[],
                spending_changes=[],
                option_id='option_999',
                total_cost=0.0
            )
        else:
            best_plan = self.rank_plans(candidates, desired_comp_dt)

        affordability_status = self._classify_affordability(
            best_plan, req_dt, safe_amt, requested_amount, earliest_full_dt, desired_comp_dt
        )

        earliest_full_str = earliest_full_dt.strftime("%Y-%m-%d") if earliest_full_dt else ""
        if affordability_status == 'affordable_now':
            earliest_full_str = req_dt_str

        return {
            'request_id': req_id,
            'amount_safe_to_pay': safe_amt,
            'affordability_status': affordability_status,
            'recommended_payment_method': best_plan.method,
            'payment_plan': best_plan.format_plan_string(),
            'earliest_date_for_full_payment': earliest_full_str,
            'spending_changes_needed': best_plan.format_spending_changes(),
            'best_plan': best_plan
        }

    def rank_plans(self, candidates, desired_comp_dt):
        def rank_key(plan):
            completes_by_deadline = (plan.end_date <= desired_comp_dt)
            no_spending_changes = (len(plan.spending_changes) == 0)
            total_cost = plan.total_cost
            start_date = plan.start_date
            num_payments = plan.num_payments
            option_id = plan.option_id

            return (
                not completes_by_deadline,
                not no_spending_changes,
                total_cost,
                start_date,
                num_payments,
                option_id
            )

        sorted_plans = sorted(candidates, key=rank_key)
        return sorted_plans[0]

    def _classify_affordability(self, plan, req_dt, safe_amt, requested_amount, earliest_full_dt, desired_comp_dt):
        if plan.method == 'not_recommended':
            if earliest_full_dt is not None and req_dt < earliest_full_dt <= (req_dt + timedelta(days=90)):
                return 'affordable_later'
            return 'not_affordable'

        if plan.method == 'full_payment' and plan.start_date == req_dt and not plan.spending_changes:
            return 'affordable_now'

        if plan.method in ['partial_payment', 'installments'] or plan.spending_changes:
            return 'affordable_with_plan'

        if plan.method == 'wait':
            return 'affordable_later'

        return 'not_affordable'

    def _generate_spending_change_plans(self, profile, future_cashflows, req_dt, requested_amount, desired_comp_dt, simulator, considered_methods):
        spending_plans = []
        stop_cats = profile['expense_categories_user_is_willing_to_stop']
        reduce_cats = profile['expense_categories_user_is_willing_to_reduce']

        flexible_events = []
        for cf in future_cashflows:
            cat = cf['category']
            evt_id = cf['event_id']
            flex = cf['flexibility']
            
            if flex in ['stoppable', 'reducible_or_stoppable'] and cat in stop_cats:
                flexible_events.append(('stop', evt_id, cf['amount'], cat))
            elif flex in ['reducible', 'reducible_or_stoppable'] and cat in reduce_cats:
                min_allowed = cf.get('minimum_allowed_amount') or (cf['amount'] * 0.5)
                flexible_events.append(('reduce_to', evt_id, min_allowed, cat))

        if flexible_events:
            for i, (action1, evt_id1, val1, cat1) in enumerate(flexible_events):
                change_str1 = f"stop:{evt_id1}" if action1 == 'stop' else f"reduce_to:{evt_id1}:{val1:.2f}".rstrip('0').rstrip('.')
                
                if 'full_payment' in considered_methods:
                    res1 = simulator.simulate(
                        candidate_payments=[{'date': req_dt, 'amount': requested_amount}],
                        spending_changes=[change_str1]
                    )
                    if res1.is_safe:
                        spending_plans.append(CandidatePlan(
                            method='full_payment',
                            payments=[{'date': req_dt, 'amount': requested_amount}],
                            spending_changes=[change_str1],
                            option_id='option_sc_full',
                            total_cost=requested_amount
                        ))

                # Also try pairs of spending changes
                for j in range(i + 1, len(flexible_events)):
                    action2, evt_id2, val2, cat2 = flexible_events[j]
                    if evt_id1 == evt_id2:
                        continue
                    change_str2 = f"stop:{evt_id2}" if action2 == 'stop' else f"reduce_to:{evt_id2}:{val2:.2f}".rstrip('0').rstrip('.')
                    
                    if 'full_payment' in considered_methods:
                        res2 = simulator.simulate(
                            candidate_payments=[{'date': req_dt, 'amount': requested_amount}],
                            spending_changes=[change_str1, change_str2]
                        )
                        if res2.is_safe:
                            spending_plans.append(CandidatePlan(
                                method='full_payment',
                                payments=[{'date': req_dt, 'amount': requested_amount}],
                                spending_changes=[change_str1, change_str2],
                                option_id='option_sc_full_pair',
                                total_cost=requested_amount
                            ))

        return spending_plans
