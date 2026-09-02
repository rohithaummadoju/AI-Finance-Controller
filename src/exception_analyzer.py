import pandas as pd


# Load reconciliation report
df = pd.read_csv("data/reconciliation_report.csv")


def analyze_exception(row):

    status = row["status"]

    if status == "PAYMENT_AMOUNT_MISMATCH":
        difference = abs(row["payment_difference"])

        return {
            "explanation": (
                f"Payment amount differs from sales amount "
                f"by ₹{difference:.2f}."
            ),
            "possible_cause": (
                "Possible causes include discount, partial payment, "
                "refund, or settlement adjustment."
            ),
            "recommended_action": (
                "Verify the payment gateway record and related invoice."
            )
        }

    elif status == "BANK_AMOUNT_MISMATCH":
        difference = abs(row["bank_difference"])

        return {
            "explanation": (
                f"Bank amount differs from sales amount "
                f"by ₹{difference:.2f}."
            ),
            "possible_cause": (
                "Possible causes include settlement fees, "
                "adjustments, or incorrect bank posting."
            ),
            "recommended_action": (
                "Compare the bank statement with the payment settlement."
            )
        }

    elif status == "PAYMENT_MISSING":

        return {
            "explanation": (
                "A sales transaction exists but no corresponding "
                "payment record was found."
            ),
            "possible_cause": (
                "Payment may have failed, been delayed, "
                "or the payment record may be missing."
            ),
            "recommended_action": (
                "Check the payment gateway for the transaction."
            )
        }

    elif status == "BANK_MISSING":

        return {
            "explanation": (
                "A sales transaction exists but no corresponding "
                "bank record was found."
            ),
            "possible_cause": (
                "Settlement may be pending or the bank record "
                "may not have been imported."
            ),
            "recommended_action": (
                "Check settlement status and bank statement."
            )
        }

    elif status == "DUPLICATE_PAYMENT":

        return {
            "explanation": (
                "Multiple payment records exist for the same "
                "transaction ID."
            ),
            "possible_cause": (
                "Possible duplicate payment or duplicate data entry."
            ),
            "recommended_action": (
                "Verify whether the customer was charged more than once."
            )
        }

    return {
        "explanation": "No exception detected.",
        "possible_cause": "None.",
        "recommended_action": "No action required."
    }


# Analyze exceptions
exceptions = df[df["status"] != "MATCH"].copy()

results = []

for _, row in exceptions.iterrows():

    analysis = analyze_exception(row)

    results.append({
        "transaction_id": row["transaction_id"],
        "status": row["status"],
        "explanation": analysis["explanation"],
        "possible_cause": analysis["possible_cause"],
        "recommended_action": analysis["recommended_action"]
    })


analysis_df = pd.DataFrame(results)


print("\n===== AI EXCEPTION ANALYSIS =====\n")

print(
    analysis_df.to_string(index=False)
)


analysis_df.to_csv(
    "data/exception_analysis.csv",
    index=False
)

print("\nAnalysis saved to:")
print("data/exception_analysis.csv")