import pandas as pd
import random
from datetime import datetime, timedelta

# -----------------------------
# 1. Generate Sales Data
# -----------------------------

random.seed(42)

transactions = []

start_date = datetime(2026, 8, 1)

for i in range(1, 101):
    transaction_id = f"TX{i:03d}"

    date = start_date + timedelta(days=random.randint(0, 20))

    customer = f"Customer_{i}"

    amount = random.choice([
        500, 750, 1000, 1500, 2000,
        2500, 3000, 5000, 7500, 10000
    ])

    transactions.append({
        "transaction_id": transaction_id,
        "date": date.strftime("%Y-%m-%d"),
        "customer": customer,
        "amount": amount
    })


sales = pd.DataFrame(transactions)

sales.to_csv("data/sales.csv", index=False)


# -----------------------------
# 2. Create Payment Data
# -----------------------------

payments = sales.copy()

payments["status"] = "success"


# Create amount mismatches
for tx_id in ["TX010", "TX025", "TX050", "TX075", "TX090"]:
    payments.loc[
        payments["transaction_id"] == tx_id,
        "amount"
    ] -= 100


# Create missing payment
payments = payments[
    payments["transaction_id"] != "TX020"
]


# Create duplicate payment
duplicate = payments[
    payments["transaction_id"] == "TX030"
]

payments = pd.concat(
    [payments, duplicate],
    ignore_index=True
)


payments.to_csv("data/payments.csv", index=False)


# -----------------------------
# 3. Create Bank Data
# -----------------------------

bank = sales.copy()

# Amount mismatches
for tx_id in ["TX040", "TX060", "TX080"]:
    bank.loc[
        bank["transaction_id"] == tx_id,
        "amount"
    ] += 150


# Missing bank transaction
bank = bank[
    bank["transaction_id"] != "TX035"
]


bank.to_csv("data/bank.csv", index=False)


print("Synthetic financial data generated successfully!")
print()
print(f"Sales records: {len(sales)}")
print(f"Payment records: {len(payments)}")
print(f"Bank records: {len(bank)}")