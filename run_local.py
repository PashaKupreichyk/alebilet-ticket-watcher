"""
Runs continuously on your own PC, checking every POLL_SECONDS.
Keeps one browser open the whole time (much faster than spinning up a
fresh browser per check), and re-checks Telegram for new commands each
cycle too.

Usage:
    python run_local.py

Stop with Ctrl+C.
"""
import os
import time
import traceback
from datetime import datetime

from playwright.sync_api import sync_playwright

from storage import load_filters, save_filters, load_state, save_state
from telegram_bot import send_message, get_new_updates
from commands import process_commands
from scraper import fetch_html_with_page, parse_offers, USER_AGENT

POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "15"))


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_cycle(page, filters, state):
    # 1. Telegram commands
    messages, new_offset = get_new_updates(state["telegram_offset"])
    state["telegram_offset"] = new_offset
    if messages:
        filters, replies = process_commands(messages, filters)
        for reply in replies:
            send_message(reply)
        save_filters(filters)
        log(f"Processed {len(messages)} command(s)")

    # 2. Check each filter
    for f in filters:
        seen = set(state["seen_ticket_ids"].get(str(f["id"]), []))
        try:
            html = fetch_html_with_page(page, f["url"])
            offers = parse_offers(html)
        except Exception:
            log(f"Error checking filter #{f['id']} ({f['url']}):")
            traceback.print_exc()
            continue

        matches = [o for o in offers if o["price"] <= f["max_price"] and o["id"] not in seen]
        for o in matches:
            log(f"MATCH filter #{f['id']}: {o['price']} PLN")
            send_message(
                f"🎟️ New ticket under {f['max_price']:.2f} PLN!\n"
                f"{o['price']:.2f} PLN - {o['label']}\n"
                f"{f['url']}"
            )
            seen.add(o["id"])

        state["seen_ticket_ids"][str(f["id"])] = list(seen)[-500:]

    save_state(state)
    return filters


def main():
    filters = load_filters()
    state = load_state()

    log(f"Starting. Polling every {POLL_SECONDS}s. {len(filters)} active filter(s).")
    send_message(f"Ticket watcher started locally (polling every {POLL_SECONDS}s).")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="pl-PL")
        page = context.new_page()

        try:
            while True:
                start = time.time()
                filters = run_cycle(page, filters, state)
                elapsed = time.time() - start
                wait = max(0.0, POLL_SECONDS - elapsed)
                time.sleep(wait)
        except KeyboardInterrupt:
            log("Stopped by user.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
