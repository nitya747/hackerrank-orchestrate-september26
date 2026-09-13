# HackerRank Orchestrate (September 2026) — Buy or Wait?

AI-powered financial decision agent built for the HackerRank Orchestrate 24-hour challenge (**Buy or Wait?**).

Given purchase or payment requests in `dataset/requests.csv`, the system reconstructs the user's complete financial state, executes a daily 90-day cash-flow simulation, evaluates candidate payment strategies (full payment, partial payment, installments, wait, or not recommended), applies permitted spending changes if needed, and outputs deterministic recommendations in `output.csv`.

---

## 1. Submission Overview

The final submission package consists of:
1. `code.zip`: Complete runnable codebase, including setup scripts, unit tests, and `evaluation/usage_report.md`.
2. `output.csv`: Complete predictions for all 250 rows in `dataset/requests.csv`.
3. `log.txt` / `chat_transcript`: Turn-by-turn agent execution log.

Mandatory submission URL:
https://www.hackerrank.com/contests/hackerrank-orchestrate-september26/challenges/buy-or-wait/submission

---

## 2. Architecture & Design Principles

```
AI/VLM Evidence Extraction (OCR images, parse text messages)
                  ↓
Deterministic Financial-State Reconstruction (resolve pending debits, settled events, linked IDs)
                  ↓
Daily 90-Day Cash-Flow Simulator (enforce minimum_balance_to_keep safety invariant)
                  ↓
Candidate Plan Generation (full, partial, installments, wait, not_recommended)
                  ↓
Deterministic Plan Ranking & Tie-breaking (exact challenge priority order)
                  ↓
Grounded Decision Explanation Generation
                  ↓
               output.csv
```

- **Deterministic Financial Engine:** Balances, 90-day forecasts, `amount_safe_to_pay`, candidate plans, ranking, and validation are computed 100% deterministically in Python.
- **Multimodal Evidence:** Unstructured receipt images and text notifications are processed for financial fact extraction without letting embedded prompt instructions override financial rules.

---

## 3. Environment & Setup

### Requirements
- Python 3.10+ (Tested on Python 3.14 on Windows `py`)
- Standard libraries: `pandas`, `numpy`, `datetime`, `re`

### Installation
No external heavy agent frameworks or vector databases are required. Install standard data manipulation libraries if needed:

```bash
pip install pandas numpy
```

---

## 4. How to Run

### Step 1: Run End-to-End Pipeline
To evaluate all requests in `dataset/requests.csv` and generate `output.csv`:

```bash
python code/main.py
```
*(On Windows, you can also run `py code/main.py`)*

### Step 2: Validate Output
To run strict schema, enum, partial payment, and safety constraint validation on `output.csv`:

```bash
python evaluation/validate_output.py output.csv
```

### Step 3: Run Public Sample Evaluation (Unit Tests)
To run accuracy evaluation against `dataset/sample_requests.csv`:

```bash
python evaluation/evaluate_samples.py
```

---

## 5. Repository Structure

```
├── AGENTS.md                  # Hackathon rules & contract specification
├── README.md                  # Project overview & execution instructions
├── log.txt                    # Mandatory turn-by-turn session log
├── output.csv                 # Generated predictions for evaluation requests
├── inspect_data.py            # Dataset inspection utility
│
├── code/
│   ├── __init__.py            # Package marker
│   ├── main.py                # Top-level pipeline entry point
│   ├── loader.py              # Loads and normalizes CSV data from dataset/
│   ├── evidence.py            # Multimodal evidence extraction & image cache
│   ├── events.py              # Financial state reconstruction & 90-day recurrence engine
│   ├── forecast.py            # Daily 90-day cash-flow simulator
│   ├── plans.py               # CandidatePlan data structures
│   ├── planner.py             # Computes safe amount, earliest date, spending changes, & ranks plans
│   └── output.py              # Formats output.csv and decision explanations
│
└── evaluation/
    ├── evaluate_samples.py    # Sample request accuracy evaluator
    ├── validate_output.py     # Strict output schema and rule validator
    └── usage_report.md        # Token usage and cost analysis report
```

---

## 6. Financial Decision & Ranking Priority

Surviving safe candidate payment plans are ranked by exact challenge priority:
1. Completes the full request by `desired_completion_date`.
2. Requires no spending changes.
3. Minimizes total amount paid (partial payment with 0 fee preferred over fee-bearing installments).
4. Starts payment earlier (earliest first payment date).
5. Uses fewer payments.
6. Lowest `payment_option_id` as final tie-breaker.
