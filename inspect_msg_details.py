import pandas as pd

msg = pd.read_csv("dataset/messages.csv")
print("=== MESSAGES WITH RELATED_EVENT_ID ===")
print(msg[msg["related_event_id"].notna()][["message_id", "user_id", "related_event_id", "source_type", "message_text"]].head(15).to_string())

print("\n=== MESSAGES WITHOUT RELATED_EVENT_ID (EMPLOYER) ===")
print(msg[msg["related_event_id"].isna() & (msg["source_type"] == "employer")][["message_id", "user_id", "message_text"]].head(15).to_string())
