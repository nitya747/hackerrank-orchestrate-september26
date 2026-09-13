import pandas as pd

fe = pd.read_csv("dataset/financial_events.csv")
img = pd.read_csv("dataset/images.csv")
msg = pd.read_csv("dataset/messages.csv")

missing_amt_fe = fe[fe["amount"].isna()]
print(f"Missing amount events count: {len(missing_amt_fe)}")
print(missing_amt_fe[["event_id", "user_id", "description", "event_date", "status"]].to_string())

merged_img = missing_amt_fe.merge(img, left_on="event_id", right_on="related_event_id")
print("\nLinked Images for Missing Amount Events:")
print(merged_img[["event_id", "user_id_x", "description", "image_id"]].to_string())

merged_msg = missing_amt_fe.merge(msg, left_on="event_id", right_on="related_event_id")
print("\nLinked Messages for Missing Amount Events:")
print(merged_msg[["event_id", "user_id_x", "description", "message_text"]].to_string())
