import pandas as pd


# ============================================================
# RECONCILIATION FUNCTION
# ============================================================

def reconcile_data(sales, payments, bank):

    # --------------------------------------------------------
    # 1. Detect duplicate payments
    # --------------------------------------------------------

    duplicate_ids = set(
        payments[
            payments.duplicated(
                subset=["transaction_id"],
                keep=False
            )
        ]["transaction_id"]
    )

    # --------------------------------------------------------
    # 2. Remove duplicate payment rows
    # --------------------------------------------------------

    payments_unique = payments.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    # --------------------------------------------------------
    # 3. Merge Sales + Payments
    # --------------------------------------------------------

    reconciliation = sales.merge(
        payments_unique[
            [
                "transaction_id",
                "amount",
                "date"
            ]
        ],
        on="transaction_id",
        how="left",
        suffixes=(
            "_sales",
            "_payment"
        )
    )

    # --------------------------------------------------------
    # 4. Merge Bank
    # --------------------------------------------------------

    reconciliation = reconciliation.merge(
        bank[
            [
                "transaction_id",
                "amount",
                "date"
            ]
        ],
        on="transaction_id",
        how="left"
    )

    # --------------------------------------------------------
    # 5. Rename Bank Columns
    # --------------------------------------------------------

    reconciliation.rename(
        columns={
            "amount": "amount_bank",
            "date": "date_bank"
        },
        inplace=True
    )

    # --------------------------------------------------------
    # 6. Determine Reconciliation Status
    # --------------------------------------------------------

    def determine_status(row):

        transaction_id = row["transaction_id"]

        # Duplicate payment
        if transaction_id in duplicate_ids:
            return "DUPLICATE_PAYMENT"

        # Payment missing
        if pd.isna(row["amount_payment"]):
            return "PAYMENT_MISSING"

        # Bank record missing
        if pd.isna(row["amount_bank"]):
            return "BANK_MISSING"

        # Payment amount mismatch
        if row["amount_sales"] != row["amount_payment"]:
            return "PAYMENT_AMOUNT_MISMATCH"

        # Bank amount mismatch
        if row["amount_sales"] != row["amount_bank"]:
            return "BANK_AMOUNT_MISMATCH"

        # Everything matches
        return "MATCH"

    reconciliation["status"] = (
        reconciliation.apply(
            determine_status,
            axis=1
        )
    )

    # --------------------------------------------------------
    # 7. Calculate Payment Difference
    # --------------------------------------------------------

    reconciliation["payment_difference"] = (
        reconciliation["amount_sales"]
        - reconciliation["amount_payment"]
    )

    # --------------------------------------------------------
    # 8. Calculate Bank Difference
    # --------------------------------------------------------

    reconciliation["bank_difference"] = (
        reconciliation["amount_sales"]
        - reconciliation["amount_bank"]
    )

    # --------------------------------------------------------
    # 9. Return Reconciliation Data
    # --------------------------------------------------------

    return reconciliation


# ============================================================
# SUMMARY FUNCTION
# ============================================================

def get_summary(df):
    total_records = len(df)

    matched_records = int(
        (df["status"] == "MATCH").sum()
    )

    exception_records = total_records - matched_records

    match_rate = (
        matched_records / total_records * 100
        if total_records > 0
        else 0
    )

    payment_discrepancy = (
        df["payment_difference"]
        .fillna(0)
        .abs()
        .sum()
    )

    bank_discrepancy = (
        df["bank_difference"]
        .fillna(0)
        .abs()
        .sum()
    )

    return {
        "total_records": total_records,
        "matched_records": matched_records,
        "exception_records": exception_records,
        "match_rate": round(match_rate, 2),
        "payment_discrepancy": round(payment_discrepancy, 2),
        "bank_discrepancy": round(bank_discrepancy, 2)
    }
from datetime import datetime
import os


def save_audit_log(summary):
    os.makedirs("data", exist_ok=True)

    log_file = "data/audit_log.txt"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"""
    ----------------------------------------
    Audit Event: Reconciliation Completed
    Action: Sales, Payments and Bank records reconciled
    Time: {timestamp}
    Total Records: {summary['total_records']}
    Matched Records: {summary['matched_records']}
    Exception Records: {summary['exception_records']}
    Match Rate: {summary['match_rate']}%
    Payment Discrepancy: ₹{summary['payment_discrepancy']:,.2f}
    Bank Discrepancy: ₹{summary['bank_discrepancy']:,.2f}
    ----------------------------------------
    """

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(log_entry)