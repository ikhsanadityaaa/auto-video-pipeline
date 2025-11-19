# scripts/notify_telegram.py
import requests
import os
import sys

TOKEN = os.environ.get("TG_TOKEN")
CHAT = os.environ.get("TG_CHAT")

def send(msg):
    if not TOKEN or not CHAT:
        print("Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}
    r = requests.post(url, data=data, timeout=10)
    print("Telegram status:", r.status_code)

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline finished"
    send(msg)
