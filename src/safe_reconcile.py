import pandas as pd
import os


def load_file(filename):
    """Safely load a CSV file."""

    path = f"data/{filename}"

    try:

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{filename} was not found"
            )

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(
                f"{filename} is empty"
            )

        print(f"✓ Loaded {filename}: {len(df)} records")

        return df

    except FileNotFoundError as e:

        print(f"⚠ WARNING: {e}")
        return None

    except pd.errors.ParserError:

        print(
            f"⚠ WARNING: {filename} is corrupted "
            "or has an invalid format."
        )

        return None

    except Exception as e:

        print(
            f"⚠ WARNING: Could not load "
            f"{filename}: {e}"
        )

        return None


# --------------------------------
# Load all sources safely
# --------------------------------

sales = load_file("sales.csv")
payments = load_file("payments.csv")
bank = load_file("bank.csv")


# --------------------------------
# Check required sources
# --------------------------------

if sales is None:

    print(
        "\n❌ CRITICAL: Sales data is unavailable."
    )

    print(
        "Reconciliation cannot continue."
    )

    exit()


# --------------------------------
# Handle missing payment data
# --------------------------------

if payments is None:

    print(
        "\n⚠ Payment data unavailable."
    )

    print(
        "All payment records will be marked "
        "for manual review."
    )

    sales["payment_status"] = "DATA_SOURCE_UNAVAILABLE"


# --------------------------------
# Handle missing bank data
# --------------------------------

if bank is None:

    print(
        "\n⚠ Bank data unavailable."
    )

    print(
        "Bank reconciliation will be skipped."
    )


# --------------------------------
# Continue if possible
# --------------------------------

print("\n==============================")
print("SAFE RECONCILIATION")
print("==============================")

print(
    f"Sales records available: {len(sales)}"
)

if payments is not None:

    print(
        f"Payment records available: {len(payments)}"
    )

else:

    print(
        "Payment records: UNAVAILABLE"
    )


if bank is not None:

    print(
        f"Bank records available: {len(bank)}"
    )

else:

    print(
        "Bank records: UNAVAILABLE"
    )


print("\nSystem completed without crashing.")