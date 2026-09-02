import os
from dotenv import load_dotenv
from google import genai

# Load .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("===== GEMINI TEST =====")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit()

print("✅ Gemini API key found.")

client = genai.Client(
    api_key=api_key
)

print("🤖 Sending request to Gemini...")

try:

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Explain financial reconciliation in one simple sentence.",
        config={
            "tools": []
        }
    )

    print("\n==============================")
    print("🤖 GEMINI RESPONSE")
    print("==============================")

    print(response.text)

    print("\n✅ Gemini is working successfully!")

except Exception as e:

    print("\n❌ Gemini request failed:")
    print(e)