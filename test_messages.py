import pandas as pd

msg = pd.read_csv("dataset/messages.csv")
print(f"Total messages: {len(msg)}")
print("Source types:", msg["source_type"].value_counts().to_dict())

# Look for key words in messages
keywords = ["salary", "gaji", "bonus", "failed", "cancelled", "cancel", "refund", "transfer", "invest", "decreased", "increased", "delay", "postponed", "arrears"]

for kw in keywords:
    matches = msg[msg["message_text"].str.contains(kw, case=False, na=False)]
    print(f"Keyword '{kw}': {len(matches)} matches")
