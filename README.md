# AI Finance Controller

An AI-powered financial reconciliation and control dashboard built with Python, Streamlit, Pandas, Plotly, and Google Gemini.

## Overview

AI Finance Controller helps finance teams reconcile financial transactions across:

- Sales records
- Payment records
- Bank records

The application automatically identifies reconciliation exceptions such as missing transactions, duplicate payments, and amount mismatches.

It also uses Google Gemini to analyze financial exceptions, generate management-level summaries, and answer finance-related questions.

## Key Features

### 1. Financial Data Upload

Upload:

- Sales data
- Payment data
- Bank transaction data

Supported formats include CSV and Excel files.

### 2. Data Validation

The application checks uploaded financial data before reconciliation and provides data-quality information.

### 3. Automated Reconciliation

The system compares Sales, Payments, and Bank records using the transaction ID.

It identifies:

- Matching transactions
- Missing payments
- Missing bank transactions
- Duplicate payments
- Payment amount mismatches
- Bank amount mismatches

### 4. Financial Dashboard

The dashboard provides:

- Total transactions
- Matched transactions
- Exception transactions
- Match rate
- Payment discrepancies
- Bank discrepancies
- Total financial impact

Interactive charts are created using Plotly.

### 5. AI Financial Analysis

Google Gemini is integrated into the application to provide:

- Management financial summaries
- Exception analysis
- Possible causes
- Recommended actions
- Priority classification

### 6. AI Finance Assistant

Users can ask questions about the reconciliation results, such as:

- Which transactions have exceptions?
- What is the match rate?
- Which transaction has the largest discrepancy?
- What is the total financial impact?
- How many payments are missing?
- Are there any duplicate payments?

### 7. Audit Trail

The application records reconciliation runs in an audit log containing:

- Timestamp
- Total records
- Matched records
- Exception records
- Match rate
- Payment discrepancy
- Bank discrepancy

### 8. Report Export

Reconciliation results can be downloaded as a CSV report.

## Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- Google Gemini API
- python-dotenv
- OpenPyXL

## Project Structure

```text
AI-Finance-Controller/
│
├── data/
│   ├── audit_log.txt
│   └── reconciliation_report.csv
│
├── src/
│   ├── dashboard.py
│   ├── reconcile.py
│   └── ai_analyzer.py
│
├── .env
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md