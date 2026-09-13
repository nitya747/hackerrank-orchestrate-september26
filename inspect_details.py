import pandas as pd

for filename in ["financial_profiles.csv", "financial_events.csv", "request_payment_options.csv", "messages.csv", "images.csv", "exchange_rates.csv"]:
    df = pd.read_csv(f"dataset/{filename}")
    print(f"=== {filename} ({len(df)} rows) ===")
    print("Columns:", list(df.columns))
    print(df.head(3).to_string())
    print("\n")
