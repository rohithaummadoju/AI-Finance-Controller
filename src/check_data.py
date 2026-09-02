import pandas as pd

sales = pd.read_csv("data/sales.csv")
payments = pd.read_csv("data/payments.csv")
bank = pd.read_csv("data/bank.csv")

print("===== SALES =====")
print(sales.head())
print("\nTotal sales records:", len(sales))

print("\n===== PAYMENTS =====")
print(payments.head())
print("\nTotal payment records:", len(payments))

print("\n===== BANK =====")
print(bank.head())
print("\nTotal bank records:", len(bank))