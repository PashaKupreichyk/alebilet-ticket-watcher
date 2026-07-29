"""
Minimal Telegram helper: send messages, read incoming commands.
Only the authorized chat (TELEGRAM_CHAT_ID) is allowed to issue commands,
so random people who find your bot's username can't add filters.
"""
import os
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(text: str):
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False},
        timeout=15,
    )


def get_new_updates(offset: int):
    """Fetch updates after `offset`. Returns (messages, new_offset)."""
    resp = requests.get(
        f"{API}/getUpdates",
        params={"offset": offset, "timeout": 0},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    messages = []
    new_offset = offset
    for update in data.get("result", []):
        new_offset = update["update_id"] + 1
        msg = update.get("message")
        if not msg:
            continue
        if str(msg.get("chat", {}).get("id")) != str(CHAT_ID):
            continue  # ignore anyone who isn't you
        text = msg.get("text", "").strip()
        if text:
            messages.append(text)
    return messages, new_offset
