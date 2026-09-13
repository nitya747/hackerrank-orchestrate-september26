import pandas as pd
import glob
import os
import sys

print("=== DATASET FILES & ROW COUNTS ===")
dataset_dir = "dataset"
for f in sorted(os.listdir(dataset_dir)):
    path = os.path.join(dataset_dir, f)
    if os.path.isfile(path):
        df = pd.read_csv(path)
        print(f"{f:30s}: {len(df):4d} rows, cols: {list(df.columns)}")

print("\n=== FINANCIAL PROFILES ===")
fp = pd.read_csv("dataset/financial_profiles.csv")
print(fp.to_string())

print("\n=== SAMPLE REQUESTS ===")
sr = pd.read_csv("dataset/sample_requests.csv")
print(sr.to_string())

print("\n=== REQUESTS ===")
req = pd.read_csv("dataset/requests.csv")
print(req.to_string())

print("\n=== FINANCIAL EVENTS UNIQUE VALUES ===")
fe = pd.read_csv("dataset/financial_events.csv")
print("Status values:", fe["status"].value_counts(dropna=False).to_dict())
print("Category values:", fe["category"].value_counts(dropna=False).to_dict())
print("Currency values:", fe["currency"].value_counts(dropna=False).to_dict())
if "is_recurring" in fe.columns:
    print("Is recurring values:", fe["is_recurring"].value_counts(dropna=False).to_dict())
if "frequency" in fe.columns:
    print("Frequency values:", fe["frequency"].value_counts(dropna=False).to_dict())

missing_amt = fe[fe["amount"].isna()]
print(f"\nMissing amount rows ({len(missing_amt)}):")
print(missing_amt[["event_id", "user_id", "description", "amount", "status"]].to_string())

print("\n=== REQUEST PAYMENT OPTIONS ===")
rpo = pd.read_csv("dataset/request_payment_options.csv")
print(rpo.to_string())

print("\n=== MESSAGES ===")
msg = pd.read_csv("dataset/messages.csv")
print(msg.to_string())

print("\n=== IMAGES ===")
img = pd.read_csv("dataset/images.csv")
print(img.to_string())

print("\n=== EXCHANGE RATES ===")
er = pd.read_csv("dataset/exchange_rates.csv")
print(er.to_string())
