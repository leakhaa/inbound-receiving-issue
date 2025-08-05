from scripts.classifier import classify_with_retry, classify
from scripts.resolver import resolve_issue
from scripts.extractor import extract_ids, validate_ids
import requests
import re
import json

# AI assistant using LLaMA model
API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"  # Secure this!
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "llama3-8b-8192"

conversation = []
chat_log = []

def chat_with_ai(user_message: str) -> str:
    conversation.append({"role": "user", "content": user_message})
    payload = {"model": MODEL, "messages": conversation, "temperature": 0.2}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    ai_message = response.json()["choices"][0]["message"]["content"]
    conversation.append({"role": "assistant", "content": ai_message})
    chat_log.append({"user": user_message, "bot": ai_message})
    print(f"🤖 {ai_message}")
    return ai_message

def is_valid_email(email):
    return re.fullmatch(r"[\w\.-]+@[\w\.-]+\.\w{2,}", email) is not None


# 1. Intro & email
chat_with_ai("You are a warehouse assistant. Start the chat with casual greeting and ask for email.no lengthly message just sharp and crisp nut be casual")
while True:
    user_email = input("You: ")
    if is_valid_email(user_email):
        chat_with_ai(f"thanks for providing your email: {user_email}.ow ask what inbound receiving issue the user is facing (ASN, PO, Pallet, Quantity Mismatch)")
        break
    else:
        chat_with_ai("Please provide a valid email address.")

# 2. Ask for the issue

# 3. Handle issue
while True:
    user_message = input("You: ")
    if user_message.lower() == "exit":
        chat_with_ai("Okay, goodbye! Have a great day.")
        break

    issue_type = classify(user_message)

    ids = extract_ids(user_message)
  #  validation_errors = validate_ids(ids)

   # if validation_errors:
   #     for err in validation_errors:
    #       chat_with_ai("Please provide valid parameter(s) again.")
    #       continue

    # chat_with_ai(f"I've identified this as: {issue_type.replace('_', ' ').title()} issue. wait until I extract the details from you and analyze them. crisp and sharp response")
    chat_with_ai(f" I'VE identified this as :{issue_type}.  working on it. Extracted details: {json.dumps(ids)} crisp and sharp straight to the point like these are the parameters do not ask for any other parameters or questions ok" )

    confirmation = resolve_issue(issue_type, ids, user_email)
    chat_with_ai(confirmation)

    followup = chat_with_ai("just ask Would you like to report another issue? Type 'exit' to quit or describe your issue.")
