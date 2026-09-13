import re
import pandas as pd

IMAGE_AMOUNT_CACHE = {
    "image_01": 4365000.0,
    "image_02": 100000.0,
    "image_03": 41272.0,
    "image_04": 2854.0,
    "image_05": 704.05,
    "image_06": 1995.0,
    "image_07": 8528.1,
    "image_08": 15339.0,
    "image_09": 723.0,
    "image_10": 79679.26,
    "image_11": 3650.0,
    "image_12": 33.5,
    "image_13": 2298.0,
    "image_14": 4543.0,
    "image_15": 9968.0,
    "image_16": 393.22,
}

class EvidenceExtractor:
    def __init__(self, loader):
        self.loader = loader
        self.image_amounts = dict(IMAGE_AMOUNT_CACHE)
        self.user_message_facts = {}
        self.process_messages()

    def get_image_amount(self, image_id):
        return self.image_amounts.get(image_id)

    def process_messages(self):
        msg_df = self.loader.messages_df
        for _, row in msg_df.iterrows():
            user_id = row['user_id']
            if user_id not in self.user_message_facts:
                self.user_message_facts[user_id] = []
            
            text = str(row['message_text'])
            sent_at = str(row['sent_at'])
            source = str(row['source_type'])
            related_event_id = row['related_event_id'] if pd.notna(row['related_event_id']) else None
            
            fact = {
                'message_id': row['message_id'],
                'user_id': user_id,
                'sent_at': sent_at,
                'source': source,
                'related_event_id': related_event_id,
                'text': text,
                'type': 'info'
            }

            # Extract specific salary updates from employer messages
            if source == 'employer':
                # Check salary date update
                m_date = re.search(r'confirmed salary is now expected on (\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
                if m_date:
                    fact['type'] = 'salary_date_change'
                    fact['new_date'] = m_date.group(1)

                # Check salary amount change
                m_sal = re.search(r'(?:salary|gaji|pay).*?(?:is|naik menjadi|reduced to|first salary will be)\s+([A-Z]{3})?\s*([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
                if m_sal:
                    curr = m_sal.group(1)
                    amt_str = m_sal.group(2).replace(',', '')
                    fact['salary_currency'] = curr
                    fact['salary_amount'] = float(amt_str)
                    fact['type'] = 'salary_amount_change'

            # Extract failed debits from bank
            elif source == 'bank':
                if 'failed' in text.lower():
                    fact['type'] = 'failed_debit_outstanding'

            self.user_message_facts[user_id].append(fact)

    def get_user_facts(self, user_id):
        return self.user_message_facts.get(user_id, [])
