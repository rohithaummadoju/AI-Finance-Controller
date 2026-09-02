import sqlite3
import pandas as pd

# Connect to SQLite database
connection = sqlite3.connect("data/finance.db")

# Load CSV files
sales = pd.read_csv("data/sales.csv")
payments = pd.read_csv("data/payments.csv")
bank = pd.read_csv("data/bank.csv")

# Store tables in SQLite
sales.to_sql(
    "sales",
    connection,
    if_exists="replace",
    index=False
)

payments.to_sql(
    "payments",
    connection,
    if_exists="replace",
    index=False
)

bank.to_sql(
    "bank",
    connection,
    if_exists="replace",
    index=False
)

connection.close()

print("Database created successfully!")
print("Tables created:")
print("- sales")
print("- payments")
print("- bank")