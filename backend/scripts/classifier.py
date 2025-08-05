import requests
import os
import re
import time

# Use environment variable or replace directly
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

VALID_LABELS = ["missing_asn", "missing_po", "missing_pallet", "quantity_mismatch", "unknown"]
MODEL = "llama3-8b-8192"  # Or "llama3-8b-instruct" if preferred

def classify(email_body: str) -> str:
    try:
        prompt = (
            "Classify the issue in the following warehouse message as one of:\n"
            "missing_asn, missing_po, missing_pallet, quantity_mismatch, unknown.\n"
            "Respond ONLY with the label, no explanation.\n\n"
            f"Email: {email_body}"
        )

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0
        }

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"].strip().lower()

        # Validate output
        for label in VALID_LABELS:
            if label == result:
                return label
        return "unknown"

    except requests.exceptions.Timeout:
        print("❌ Classification request timed out.")
        return "unknown"
    except Exception as e:
        print("❌ Classification error:", e)
        return "unknown"

def classify_with_retry(email_body: str, retries=2, delay=3):
    for attempt in range(retries):
        label = classify(email_body)
        if label != "unknown":
            return label
        print(f"⚠️ Retry {attempt + 1}/{retries} after {delay}s...")
        time.sleep(delay)
    return "unknown"
