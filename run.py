"""
Entry point run on a schedule by GitHub Actions:
  1. Read any new Telegram commands (/watch, /list, /remove) and update filters.json
  2. For each active filter, scrape the event page and alert on new offers <= max_price
  3. Persist filters.json and state.json (the workflow commits these back to the repo)
"""
import sys
import traceback

from storage import load_filters, save_filters, load_state, save_state
from telegram_bot import send_message, get_new_updates
from commands import process_commands
from scraper import fetch_html, parse_offers


def main():
    filters = load_filters()
    state = load_state()

    # 1. Process any new commands sent to the bot
    messages, new_offset = get_new_updates(state["telegram_offset"])
    state["telegram_offset"] = new_offset
    if messages:
        filters, replies = process_commands(messages, filters)
        for reply in replies:
            send_message(reply)

    # 2. Check each filter for new matching offers
    for f in filters:
        seen = set(state["seen_ticket_ids"].get(str(f["id"]), []))
        try:
            html = fetch_html(f["url"])
            offers = parse_offers(html)
        except Exception:
            print(f"Error checking filter #{f['id']}: {f['url']}", file=sys.stderr)
            traceback.print_exc()
            continue

        matches = [o for o in offers if o["price"] <= f["max_price"] and o["id"] not in seen]
        for o in matches:
            send_message(
                f"🎟️ New ticket under {f['max_price']:.2f} PLN!\n"
                f"{o['price']:.2f} PLN - {o['label']}\n"
                f"{f['url']}"
            )
            seen.add(o["id"])

        # Keep the seen-set from growing forever: cap at last 500 ids
        state["seen_ticket_ids"][str(f["id"])] = list(seen)[-500:]

    save_filters(filters)
    save_state(state)


if __name__ == "__main__":
    main()
