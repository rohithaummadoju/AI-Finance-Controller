import os
import pandas as pd
from dotenv import load_dotenv
from google import genai

# --------------------------------
# Load environment variables
# --------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY not found in .env"
    )

# --------------------------------
# Create Gemini client
# --------------------------------

client = genai.Client(
    api_key=api_key
)

# --------------------------------
# Load reconciliation data
# --------------------------------

df = pd.read_csv(
    "data/reconciliation_report.csv"
)

# --------------------------------
# Prepare financial data
# --------------------------------

finance_data = df[
    [
        "transaction_id",
        "amount_sales",
        "amount_payment",
        "amount_bank",
        "status",
        "payment_difference",
        "bank_difference"
    ]
].to_string(index=False)


# --------------------------------
# Finance AI
# --------------------------------

def ask_finance_ai(question):

    prompt = f"""
You are an AI Finance Controller.

Analyze the provided reconciliation data
and answer the user's question.

IMPORTANT RULES:

1. Use ONLY the provided data.
2. Never invent transaction IDs.
3. Never invent financial amounts.
4. If information is unavailable, say so.
5. Identify transactions requiring manual review.
6. Explain discrepancies clearly.
7. Give practical finance recommendations.
8. Do not claim that money was recovered unless
   the data explicitly shows recovery.

RECONCILIATION DATA:

{finance_data}


USER QUESTION:

{question}


Give a concise, professional finance answer.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


# --------------------------------
# Interactive test
# --------------------------------

if __name__ == "__main__":

    print("=" * 50)
    print("🤖 AI FINANCE CONTROLLER")
    print("=" * 50)

    question = input(
        "\nAsk a finance question: "
    )

    try:

        answer = ask_finance_ai(question)

        print("\n===== AI ANSWER =====")
        print(answer)

    except Exception as e:

        print("\n❌ AI service unavailable.")
        print("Error:", e)