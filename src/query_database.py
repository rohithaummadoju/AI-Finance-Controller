import sqlite3
import pandas as pd

connection = sqlite3.connect("data/finance.db")

query = """
SELECT *
FROM sales
LIMIT 10
"""

result = pd.read_sql_query(
    query,
    connection
)

print(result)

connection.close()