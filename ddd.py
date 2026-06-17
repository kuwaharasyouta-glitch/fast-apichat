import requests
import os

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": os.environ["GEMINI_API_KEY"]
}

payload = {
    "contents": [{
        "parts": [{
            "text": "こんにちは"
        }]
    }]
}

r = requests.post(url, headers=headers, json=payload, timeout=30)

print(r.status_code)
print(r.text)