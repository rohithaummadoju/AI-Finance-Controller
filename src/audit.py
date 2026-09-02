import pandas as pd
from datetime import datetime

# Load reconciliation report
df = pd.read_csv("data/reconciliation_report.csv")

audit_records = []

for _, row in df.iterrows():

    status = row["status"]

    if status == "MATCH":
        action = "No action required"
        reason = "Sales, payment and bank amounts matched"

    elif status == "PAYMENT_AMOUNT_MISMATCH":
        action = "Manual review"
        reason = "Payment amount differs from sales amount"

    elif status == "BANK_AMOUNT_MISMATCH":
        action = "Manual review"
        reason = "Bank amount differs from sales amount"

    elif status == "PAYMENT_MISSING":
        action = "Investigate payment"
        reason = "No payment record found"

    elif status == "BANK_MISSING":
        action = "Investigate settlement"
        reason = "No bank record found"

    elif status == "DUPLICATE_PAYMENT":
        action = "Verify duplicate"
        reason = "Multiple payment records found"

    else:
        action = "Manual review"
        reason = "Unknown exception"

    audit_records.append({
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "transaction_id": row["transaction_id"],
        "status": status,
        "action": action,
        "reason": reason
    })


audit_df = pd.DataFrame(audit_records)

audit_df.to_csv(
    "data/audit_log.csv",
    index=False
)

print("Audit trail created successfully!")

print("\n===== AUDIT TRAIL =====")

print(
    audit_df.head(20).to_string(index=False)
)