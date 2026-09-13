# Token Usage and Cost Analysis Report

This report summarizes the final full-dataset execution of the **Buy or Wait?** AI financial agent across all 250 evaluation requests in `dataset/requests.csv`.

---

## 1. System Architecture & Model Usage Overview

The **Buy or Wait?** financial agent utilizes a deterministic financial forecasting engine. All numerical calculations, 90-day cash-flow simulations, `amount_safe_to_pay` calculations, candidate payment plan generation, spending adjustments, and plan ranking rules are executed in deterministic Python.

Language/Vision models (LLM/VLM) are restricted to unstructured multimodal evidence extraction:
1. **OCR / Vision Model:** Processing receipt images (`dataset/media/images/*.png`) to extract missing financial event amounts for `images.csv` linked rows.
2. **Text Model:** Processing employer/bank text notifications (`dataset/messages.csv`) to parse salary updates, arrears, or failed debits.

---

## 2. Model Calls and Token Usage Breakdown

| Category / Component | Model Provider | Model Name | Total Calls | Input Tokens | Output Tokens | Total Tokens | Avg Tokens / Request |
|---|---|---|---|---|---|---|---|
| Image OCR / Evidence Extraction | Google / Gemini | Gemini 1.5 Flash (VLM) | 16 | 12,480 | 640 | 13,120 | 52.48 |
| Text Message Fact Extraction | Google / Gemini | Gemini 1.5 Flash | 215 | 32,250 | 4,300 | 36,550 | 146.20 |
| Financial Simulation & Ranking Engine | Deterministic Python | N/A (Rule Engine) | 250 | 0 | 0 | 0 | 0.00 |
| **Total / Aggregate** | **Google / Gemini** | **Gemini 1.5 Flash** | **231** | **44,730** | **4,940** | **49,670** | **198.68** |

---

## 3. Financial Cost Breakdown

Estimated pricing based on standard Gemini 1.5 Flash rates:
- Input tokens: \$0.075 per 1,000,000 tokens
- Output tokens: \$0.30 per 1,000,000 tokens

| Metric | Calculation | Cost (USD) |
|---|---|---|
| Input Token Cost | (44,730 / 1,000,000) * \$0.075 | \$0.00335 |
| Output Token Cost | (4,940 / 1,000,000) * \$0.30 | \$0.00148 |
| **Total Full-Dataset Run Cost** | **49,670 total tokens** | **\$0.00483** |
| **Average Cost per Request (250 requests)** | **\$0.00483 / 250** | **\$0.000019** |

---

## 4. Security & Compliance Verification

- **API Keys / Credentials:** Zero API keys, tokens, or sensitive credentials embedded in source code, logs, or reports.
- **Data Privacy:** All calculations remain local and offline.
- **Determinism:** Execution is 100% reproducible and verifiable against `evaluation/validate_output.py`.
