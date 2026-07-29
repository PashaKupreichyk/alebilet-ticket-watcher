# Alebilet.pl Ticket Watcher

Telegram bot that watches Alebilet.pl events and pings you the moment a
ticket appears at or under a price you set — configured entirely through
Telegram chat commands, no code edits needed.

## Setup (one time)

1. **Create a GitHub repo** (private is fine) and push these files to it.

2. **Add two repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `TELEGRAM_BOT_TOKEN` — your bot token from @BotFather
   - `TELEGRAM_CHAT_ID` — your Telegram chat id

3. **Enable Actions** for the repo (Actions tab → enable if prompted). The
   workflow runs automatically every 5 minutes, or you can trigger it
   manually from the Actions tab (`Run workflow`) to test.

## Using the bot

Message your bot in Telegram (must be from the chat you set as
`TELEGRAM_CHAT_ID` — anyone else's commands are ignored):

```
/watch https://www.alebilet.pl/wydarzenie/xyz 250
```
→ notifies you when a ticket for that event appears at or below 250 PLN.

```
/list
```
→ shows your active filters with their ids.

```
/remove 2
```
→ deletes filter #2.

Replies to your commands only show up after the next scheduled run
(within 5 minutes), since there's no server listening in real time —
GitHub Actions checks in on a timer instead.

## Running locally instead (faster polling)

GitHub Actions can't reliably poll faster than every several minutes, which
is too slow for high-demand tickets. `run_local.py` runs continuously on
your own always-on PC instead, checking every 15 seconds by default (one
browser stays open the whole time, so each check is fast).

**Windows setup:**
1. Install [Python 3.11+](https://www.python.org/downloads/) if you don't have it (check "Add to PATH" during install)
2. Put this whole `ticket-watcher` folder somewhere permanent
3. Open `start_windows.bat` in a text editor, replace `PASTE_YOUR_TOKEN_HERE` with your real bot token
4. Double-click `start_windows.bat`
   - First run installs dependencies + a headless Chromium browser (~1-2 min)
   - After that it starts polling immediately
5. Leave the window open (minimized is fine) — closing it stops the watcher
6. Message the bot `/watch <link> <price>` any time; it'll pick up new commands within one poll cycle (~15s)

**To run it automatically at Windows startup** (optional): press `Win+R`,
type `shell:startup`, hit enter, then drop a shortcut to `start_windows.bat`
into that folder.

You still get `/watch`, `/list`, `/remove` exactly as before — same
`filters.json`/`state.json` files, just checked locally instead of via
GitHub Actions. (You can run both `run_local.py` and the GitHub Actions
workflow if you want a redundant slower backup, but they'd need separate
filters/state since they don't share storage.)

## ⚠️ One thing to calibrate

Alebilet.pl's bot-detection blocked even read-only access while I was
building this, so I couldn't see their real page markup to write exact
CSS selectors — `scraper.py` currently uses a best-effort generic
approach (looks for likely offer containers, falls back to scanning for
"XX zł" price patterns).

**To calibrate it:** once you have a real event URL, run locally:
```
pip install -r requirements.txt
playwright install --with-deps chromium
python scraper.py "<event_url>" --debug
```
This dumps `debug_page.html` and `debug_screenshot.png`. Send me those
(or just describe what the ticket listings look like) and I'll tighten
the selectors in `scraper.py` so it reliably picks up individual ticket
offers instead of the generic fallback.

## Files
- `run.py` — orchestrator run each cycle by GitHub Actions
- `scraper.py` — Playwright-based page fetch + offer parsing
- `commands.py` — /watch, /list, /remove command handling
- `telegram_bot.py` — sending messages / reading incoming commands
- `storage.py` — filters.json / state.json persistence
- `.github/workflows/watch.yml` — the schedule
