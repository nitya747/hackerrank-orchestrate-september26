import pandas as pd
from datetime import datetime

fe = pd.read_csv("dataset/financial_events.csv")
fp = pd.read_csv("dataset/financial_profiles.csv")
req = pd.read_csv("dataset/requests.csv")

fe_user = fe.merge(fp[['user_id', 'home_currency']], on='user_id')

print("=== EVENT TYPES ===")
print(fe['event_type'].value_counts(dropna=False).to_dict())

print("\n=== CATEGORIES ===")
print(fe['category'].value_counts(dropna=False).to_dict())

print("\n=== DIRECTIONS ===")
print(fe['direction'].value_counts(dropna=False).to_dict())

print("\n=== FLEXIBILITY ===")
print(fe['flexibility'].value_counts(dropna=False).to_dict())

# Analyze recurring events for user_01
fe_u1 = fe[fe['user_id'] == 'user_01'].sort_values('event_date')
print("\n=== USER_01 SAMPLE EVENTS ===")
print(fe_u1[['event_id', 'description', 'category', 'direction', 'amount', 'currency', 'event_date', 'status', 'flexibility']].tail(15).to_string())
