"""
Parses Telegram commands and updates the filters list.

Supported commands:
  /watch <alebilet.pl event URL> <max_price>   e.g. /watch https://www.alebilet.pl/wydarzenie/xyz 250
  /list                                        show active filters
  /remove <id>                                 delete a filter
  /help                                        show usage
"""
import re
from storage import next_filter_id

HELP_TEXT = (
    "Commands:\n"
    "/watch <alebilet.pl event link> <max_price> - notify me when a ticket "
    "for this event appears at or below max_price (PLN)\n"
    "/list - show active filters\n"
    "/remove <id> - remove a filter\n"
)


def process_commands(messages, filters):
    """Mutates and returns (filters, list_of_reply_strings)."""
    replies = []
    for text in messages:
        parts = text.split()
        cmd = parts[0].lower()

        if cmd == "/start" or cmd == "/help":
            replies.append(HELP_TEXT)

        elif cmd == "/watch":
            if len(parts) < 3:
                replies.append("Usage: /watch <alebilet.pl link> <max_price>")
                continue
            url = parts[1]
            price_str = parts[2].replace(",", ".")
            if "alebilet.pl" not in url:
                replies.append("That doesn't look like an alebilet.pl link.")
                continue
            try:
                max_price = float(re.sub(r"[^\d.]", "", price_str))
            except ValueError:
                replies.append("Couldn't parse the price. Example: /watch <link> 250")
                continue
            new_filter = {
                "id": next_filter_id(filters),
                "url": url,
                "max_price": max_price,
            }
            filters.append(new_filter)
            replies.append(
                f"Watching (id {new_filter['id']}): {url} for tickets <= {max_price:.2f} PLN"
            )

        elif cmd == "/list":
            if not filters:
                replies.append("No active filters. Add one with /watch <link> <price>.")
            else:
                lines = [
                    f"#{f['id']}: {f['url']} <= {f['max_price']:.2f} PLN" for f in filters
                ]
                replies.append("Active filters:\n" + "\n".join(lines))

        elif cmd == "/remove":
            if len(parts) < 2:
                replies.append("Usage: /remove <id>")
                continue
            try:
                fid = int(parts[1])
            except ValueError:
                replies.append("id must be a number, see /list")
                continue
            before = len(filters)
            filters[:] = [f for f in filters if f["id"] != fid]
            if len(filters) < before:
                replies.append(f"Removed filter #{fid}")
            else:
                replies.append(f"No filter with id {fid}. See /list")

        else:
            replies.append("Unknown command. " + HELP_TEXT)

    return filters, replies
