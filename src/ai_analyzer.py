import os
import time
import pandas as pd

from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")


# ============================================================
# GEMINI CLIENT
# ============================================================

if api_key:
    client = genai.Client(
        api_key=api_key
    )
else:
    client = None


# ============================================================
# GEMINI REQUEST WITH RETRY
# ============================================================

def generate_with_retry(prompt):
    
    if client is None:
        return None, (
            "❌ GEMINI_API_KEY was not found.\n\n"
            "Please check your .env file."
        )

    max_attempts = 2

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config={
                    "tools": [],
                    "thinking_config": {
            "thinking_level": "minimal"
        }
                }
            )

            return response.text, None

        except Exception as e:

            error_text = str(e)

            # ------------------------------------------------
            # Temporary Gemini server overload
            # ------------------------------------------------

            if "503" in error_text:

                if attempt < max_attempts - 1:

                    wait_time = 3

                    time.sleep(
                        wait_time
                    )

                    continue

                return None, (
                    "❌ Gemini is temporarily unavailable "
                    "because the model is experiencing high demand.\n\n"
                    "The application automatically retried "
                    "the request several times. Please try again "
                    "after a short while."
                )

            # ------------------------------------------------
            # Rate limit / quota
            # ------------------------------------------------

            if "429" in error_text:

                return None, (
                    "❌ Gemini request limit or quota was reached.\n\n"
                    "Please check your Gemini API usage and quota."
                )

            # ------------------------------------------------
            # Authentication error
            # ------------------------------------------------

            if "401" in error_text or "403" in error_text:

                return None, (
                    "❌ Gemini API authentication failed.\n\n"
                    "Please check your GEMINI_API_KEY."
                )

            # ------------------------------------------------
            # Model not found
            # ------------------------------------------------

            if "404" in error_text:

                return None, (
                    "❌ Gemini model was not found or is unavailable "
                    "for this API key.\n\n"
                    "Please check the model name."
                )

            # ------------------------------------------------
            # Other error
            # ------------------------------------------------

            return None, (
                "❌ Gemini request failed.\n\n"
                f"Error: {e}"
            )

    return None, (
        "❌ Gemini request failed after multiple attempts."
    )

# ============================================================
# ANALYZE ONE FINANCIAL EXCEPTION
# ============================================================

def analyze_exception(row):

    if client is None:

        return (
            "❌ GEMINI_API_KEY was not found.\n\n"
            "Please check your .env file."
        )

    # --------------------------------------------------------
    # Get transaction information
    # --------------------------------------------------------

    transaction_id = str(
        row.get(
            "transaction_id",
            "Unknown"
        )
    )

    status = str(
        row.get(
            "status",
            "Unknown"
        )
    )

    sales_amount = row.get(
        "amount_sales"
    )

    payment_amount = row.get(
        "amount_payment"
    )

    bank_amount = row.get(
        "amount_bank"
    )

    payment_difference = row.get(
        "payment_difference"
    )

    bank_difference = row.get(
        "bank_difference"
    )

    # --------------------------------------------------------
    # Handle missing values
    # --------------------------------------------------------

    if pd.isna(payment_amount):

        payment_text = "Missing"

    else:

        payment_text = (
            f"₹{payment_amount:,.2f}"
        )

    if pd.isna(bank_amount):

        bank_text = "Missing"

    else:

        bank_text = (
            f"₹{bank_amount:,.2f}"
        )

    if pd.isna(payment_difference):

        payment_difference_text = "N/A"

    else:

        payment_difference_text = (
            f"₹{payment_difference:,.2f}"
        )

    if pd.isna(bank_difference):

        bank_difference_text = "N/A"

    else:

        bank_difference_text = (
            f"₹{bank_difference:,.2f}"
        )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI Finance Controller.

Analyze this financial reconciliation exception.

Transaction ID:
{transaction_id}

Reconciliation Status:
{status}

Sales Amount:
₹{sales_amount:,.2f}

Payment Amount:
{payment_text}

Bank Amount:
{bank_text}

Payment Difference:
{payment_difference_text}

Bank Difference:
{bank_difference_text}

Provide the analysis using these sections:

### 1. Direct Explanation

Explain why this transaction is an exception.

### 2. Financial Impact

Explain the amount involved and which financial
source differs.

### 3. Possible Causes

Give reasonable possible causes.

Clearly state that these are possible explanations,
not confirmed facts.

### 4. Recommended Action

Give practical steps that the finance/reconciliation
team should take.

### 5. Priority

Classify the issue as:

LOW
MEDIUM
HIGH

Use the following data-based guidance:

- HIGH:
  Missing financial records, duplicate payments,
  or significant financial discrepancies that require
  prompt investigation.

- MEDIUM:
  Amount mismatches or other discrepancies that have
  a measurable financial impact but do not indicate
  a missing financial record.

- LOW:
  Minor discrepancies with limited financial impact.

Briefly explain why the selected priority applies
to this specific transaction.

Do not assign priority based on assumptions about
the business. Use the transaction's actual status
and financial differences.

Important rules:

- Use only the financial information provided.
- Do not invent transaction information.
- Do not invent amounts.
- Do not present possible causes as confirmed facts.
- Do not modify financial records.
"""

    # --------------------------------------------------------
    # Send to Gemini
    # --------------------------------------------------------

    answer, error = generate_with_retry(
        prompt
    )

    if error:
        return error

    return answer


# ============================================================
# AI FINANCIAL SUMMARY
# ============================================================

def generate_finance_summary(reconciliation_df):

    if client is None:

        return (
            "❌ GEMINI_API_KEY was not found.\n\n"
            "Please check your .env file."
        )

    if reconciliation_df is None:

        return (
            "❌ No reconciliation data is available."
        )

    if reconciliation_df.empty:

        return (
            "❌ The reconciliation dataset is empty."
        )

    # --------------------------------------------------------
    # Calculate summary information
    # --------------------------------------------------------

    total_records = len(
        reconciliation_df
    )

    matched = int(
        (
            reconciliation_df["status"] == "MATCH"
        ).sum()
    )

    exceptions = (
        total_records - matched
    )

    match_rate = (
        matched / total_records * 100
        if total_records > 0
        else 0
    )

    payment_discrepancy = (
        reconciliation_df["payment_difference"]
        .fillna(0)
        .abs()
        .sum()
    )

    bank_discrepancy = (
        reconciliation_df["bank_difference"]
        .fillna(0)
        .abs()
        .sum()
    )

    total_financial_impact = (
        payment_discrepancy
        + bank_discrepancy
    )

    # --------------------------------------------------------
    # Exception breakdown
    # --------------------------------------------------------

    exception_counts = (
        reconciliation_df[
            reconciliation_df["status"] != "MATCH"
        ]["status"]
        .value_counts()
        .to_dict()
    )

    # --------------------------------------------------------
    # Find highest-impact transactions
    # --------------------------------------------------------

    impact_df = reconciliation_df.copy()

    impact_df["total_difference"] = (
        impact_df["payment_difference"]
        .fillna(0)
        .abs()
        +
        impact_df["bank_difference"]
        .fillna(0)
        .abs()
    )

    top_exceptions = (
        impact_df[
            impact_df["status"] != "MATCH"
        ]
        .sort_values(
            "total_difference",
            ascending=False
        )
        .head(5)
    )

    if not top_exceptions.empty:

        columns = [
            "transaction_id",
            "status",
            "amount_sales",
            "amount_payment",
            "amount_bank",
            "total_difference"
        ]

        top_exception_text = (
            top_exceptions[columns]
            .to_string(index=False)
        )

    else:

        top_exception_text = (
            "No financial exceptions were found."
        )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an experienced AI Finance Controller.

Prepare a concise, professional management-level
financial reconciliation summary using ONLY the
data provided below.

==================================================
RECONCILIATION OVERVIEW
==================================================

Total Records:
{total_records}

Matched Records:
{matched}

Exceptions:
{exceptions}

Match Rate:
{match_rate:.2f}%

Payment Discrepancy:
₹{payment_discrepancy:,.2f}

Bank Discrepancy:
₹{bank_discrepancy:,.2f}

Total Financial Impact:
₹{total_financial_impact:,.2f}


==================================================
EXCEPTION BREAKDOWN
==================================================

{exception_counts}


==================================================
TOP FINANCIAL IMPACT TRANSACTIONS
==================================================

{top_exception_text}


==================================================
REQUIRED OUTPUT FORMAT
==================================================

### 📊 Executive Summary

Provide a short management-level overview of the
reconciliation results.

Mention:

- Total records
- Match rate
- Number of exceptions
- Overall financial impact


### 🔎 Key Findings

List the most important confirmed findings from
the reconciliation data.

Use bullet points.


### 💰 Financial Impact

Clearly explain:

- Payment discrepancy amount
- Bank discrepancy amount
- Total financial impact

Use the exact amounts provided.


### 🚨 Risk Assessment

Classify the overall reconciliation risk as:

LOW
MEDIUM
HIGH

Then briefly explain the classification using
only the available financial data.

Do not invent business risks that are not supported
by the data.


### ✅ Recommended Actions

Provide practical actions for the finance team.

Prioritize:

1. Missing transactions
2. Amount mismatches
3. Duplicate payments
4. High-impact exceptions

Do not claim that an issue has been resolved unless
the data confirms it.


### 📌 Management Attention

State whether the reconciliation contains items
that require management review.

Explain the reason using the actual data.


==================================================
IMPORTANT RULES
==================================================

1. Use ONLY the provided reconciliation data.

2. Do not invent transactions.

3. Do not invent financial amounts.

4. Do not invent causes.

5. Clearly distinguish confirmed findings from
   possible explanations.

6. Possible causes must be explicitly described as
   possible, not confirmed.

7. Use the exact financial amounts provided.

8. Do not modify financial records.

9. Keep the response concise and professional.

10. Write for a finance manager reviewing the
    reconciliation results.

11. Do not provide generic financial advice unrelated
    to the reconciliation data.
"""

    # --------------------------------------------------------
    # Send to Gemini
    # --------------------------------------------------------

    answer, error = generate_with_retry(
        prompt
    )

    if error:
        return error

    return answer


# ============================================================
# AI FINANCE ASSISTANT
# ============================================================

def ask_finance_assistant(
    question,
    reconciliation_df
):

    # --------------------------------------------------------
    # Check Gemini
    # --------------------------------------------------------

    if client is None:

        return (
            "❌ GEMINI_API_KEY was not found.\n\n"
            "Please check your .env file."
        )

    # --------------------------------------------------------
    # Check question
    # --------------------------------------------------------

    if not question:

        return (
            "❌ Please enter a finance question."
        )

    # --------------------------------------------------------
    # Check data
    # --------------------------------------------------------

    if reconciliation_df is None:

        return (
            "❌ No reconciliation data is available."
        )

    if reconciliation_df.empty:

        return (
            "❌ The reconciliation dataset is empty."
        )

    # --------------------------------------------------------
    # Calculate summary
    # --------------------------------------------------------

    total_records = len(
        reconciliation_df
    )

    matched = int(
        (
            reconciliation_df["status"] == "MATCH"
        ).sum()
    )

    exceptions = (
        total_records - matched
    )

    match_rate = (
        matched / total_records * 100
        if total_records > 0
        else 0
    )

    # --------------------------------------------------------
    # Prepare reconciliation data
    # --------------------------------------------------------

    data_for_ai = (
        reconciliation_df
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI Finance Controller.

A user has uploaded financial reconciliation data
containing Sales, Payments and Bank records.

Answer the user's question using ONLY the data
provided below.

==================================================
USER QUESTION
==================================================

{question}


==================================================
RECONCILIATION SUMMARY
==================================================

Total Records:
{total_records}

Matched Records:
{matched}

Exceptions:
{exceptions}

Match Rate:
{match_rate:.2f}%


==================================================
RECONCILIATION DATA
==================================================

{data_for_ai}


==================================================
IMPORTANT RULES
==================================================

1. Use only the provided reconciliation data.

2. Do not invent transactions.

3. Do not invent financial amounts.

4. If information is missing, clearly say it is missing.

5. Clearly distinguish confirmed facts from possible
   explanations.

6. If the question asks about a transaction, use the
   actual values from the dataset.

7. If the question asks for recommendations, provide
   practical finance/reconciliation actions.

8. If the user asks about the largest discrepancy,
   compare the actual differences in the dataset.

9. If multiple transactions have the same largest
   discrepancy, mention all relevant transactions.

10. Do not modify financial records.

11. Keep the answer clear and finance-oriented.
"""

    # --------------------------------------------------------
    # Send to Gemini
    # --------------------------------------------------------

    answer, error = generate_with_retry(
        prompt
    )

    if error:
        return error

    return answer