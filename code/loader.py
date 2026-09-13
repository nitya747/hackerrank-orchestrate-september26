import os
import pandas as pd
from datetime import datetime, date

class DataLoader:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir
        self.requests_df = None
        self.sample_requests_df = None
        self.profiles_df = None
        self.events_df = None
        self.payment_options_df = None
        self.messages_df = None
        self.images_df = None
        self.exchange_rates_df = None
        self.exchange_rate_map = {}
        
        self.load_all()

    def load_all(self):
        self.requests_df = pd.read_csv(os.path.join(self.dataset_dir, "requests.csv"))
        if os.path.exists(os.path.join(self.dataset_dir, "sample_requests.csv")):
            self.sample_requests_df = pd.read_csv(os.path.join(self.dataset_dir, "sample_requests.csv"))
        self.profiles_df = pd.read_csv(os.path.join(self.dataset_dir, "financial_profiles.csv"))
        self.events_df = pd.read_csv(os.path.join(self.dataset_dir, "financial_events.csv"))
        self.payment_options_df = pd.read_csv(os.path.join(self.dataset_dir, "request_payment_options.csv"))
        self.messages_df = pd.read_csv(os.path.join(self.dataset_dir, "messages.csv"))
        self.images_df = pd.read_csv(os.path.join(self.dataset_dir, "images.csv"))
        self.exchange_rates_df = pd.read_csv(os.path.join(self.dataset_dir, "exchange_rates.csv"))

        self._build_exchange_rate_map()

    def _build_exchange_rate_map(self):
        self.exchange_rate_map = {}
        for _, row in self.exchange_rates_df.iterrows():
            d = str(row['rate_date']).strip()
            fc = str(row['from_currency']).strip()
            tc = str(row['to_currency']).strip()
            rate = float(row['rate'])
            self.exchange_rate_map[(d, fc, tc)] = rate
            if rate != 0:
                self.exchange_rate_map[(d, tc, fc)] = 1.0 / rate

    def convert_currency(self, amount, from_currency, to_currency, settlement_date):
        if amount is None or pd.isna(amount):
            return None
        from_curr = str(from_currency).strip()
        to_curr = str(to_currency).strip()
        if from_curr == to_curr:
            return float(amount)
        
        date_str = str(settlement_date).split('T')[0].strip()
        key = (date_str, from_curr, to_curr)
        if key in self.exchange_rate_map:
            return float(amount) * self.exchange_rate_map[key]
        
        # Fallback: look for closest date for the currency pair
        matching_rates = [
            (abs((datetime.strptime(d, "%Y-%m-%d") - datetime.strptime(date_str, "%Y-%m-%d")).days), r)
            for (d, fc, tc), r in self.exchange_rate_map.items()
            if fc == from_curr and tc == to_curr
        ]
        if matching_rates:
            matching_rates.sort(key=lambda x: x[0])
            return float(amount) * matching_rates[0][1]
        
        return float(amount)

    def get_user_profile(self, user_id):
        user_rows = self.profiles_df[self.profiles_df['user_id'] == user_id]
        if user_rows.empty:
            return None
        row = user_rows.iloc[0].to_dict()
        
        def parse_list(val):
            if pd.isna(val) or not val:
                return []
            return [x.strip() for x in str(val).split('|') if x.strip()]

        row['financial_priorities'] = parse_list(row.get('financial_priorities'))
        row['expense_categories_to_protect'] = parse_list(row.get('expense_categories_to_protect'))
        row['expense_categories_user_is_willing_to_reduce'] = parse_list(row.get('expense_categories_user_is_willing_to_reduce'))
        row['expense_categories_user_is_willing_to_stop'] = parse_list(row.get('expense_categories_user_is_willing_to_stop'))
        row['payment_methods_user_will_consider'] = parse_list(row.get('payment_methods_user_will_consider'))
        row['max_installment_months'] = float(row['max_installment_months']) if pd.notna(row.get('max_installment_months')) else None
        
        return row
