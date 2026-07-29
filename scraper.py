"""
Fetches an Alebilet.pl event page with a real (headless) browser, since the
site blocks plain HTTP requests, and extracts individual ticket offers.

NOTE: Alebilet's exact markup wasn't available to inspect while building this
(their bot-protection blocked even read-only fetches during development), so
the CSS selectors below are a best-effort guess based on typical resale-site
markup. Run `python scraper.py <event_url> --debug` once you have a real
event link to dump the page HTML/screenshot, then adjust SELECTORS below to
match. This is the one part of the project that will likely need a quick
calibration pass.
"""
import hashlib
import re
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

PRICE_RE = re.compile(r"(\d[\d\s]*[.,]?\d*)\s*zł")


def fetch_html(url: str, debug: bool = False) -> str:
    """One-off fetch: launches and tears down a fresh browser. Fine for
    occasional/CI use, too slow to call every 15s in a tight loop -- use
    fetch_html_with_page() + a long-lived page for that instead."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="pl-PL")
        page = context.new_page()
        html = fetch_html_with_page(page, url, debug=debug)
        browser.close()
    return html


def fetch_html_with_page(page, url: str, debug: bool = False) -> str:
    """Reuses an already-open Playwright page (much faster for polling
    loops, since we skip browser/context startup on every check)."""
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)  # let any lazy-loaded offers render
    html = page.content()
    if debug:
        page.screenshot(path="debug_screenshot.png", full_page=True)
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
    return html


def parse_offers(html: str):
    """
    Returns a list of dicts: {id, price, label}
    `id` is a stable hash so we can tell "new" offers from ones we've
    already alerted on, without needing to know Alebilet's real IDs.
    """
    soup = BeautifulSoup(html, "lxml")

    # Best-effort: look for likely offer containers first (adjust after calibration)
    candidates = soup.select(
        "[class*='offer'], [class*='ticket'], [class*='listing'], [data-testid*='offer']"
    )
    if not candidates:
        candidates = soup.find_all(string=PRICE_RE)
        candidates = [c.parent for c in candidates]

    offers = []
    seen_text = set()
    for el in candidates:
        text = el.get_text(" ", strip=True)
        if not text or text in seen_text:
            continue
        seen_text.add(text)
        m = PRICE_RE.search(text)
        if not m:
            continue
        price_str = m.group(1).replace(" ", "").replace(",", ".")
        try:
            price = float(price_str)
        except ValueError:
            continue
        offer_id = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        offers.append({"id": offer_id, "price": price, "label": text[:200]})

    return offers


if __name__ == "__main__":
    url = sys.argv[1]
    debug = "--debug" in sys.argv
    html = fetch_html(url, debug=debug)
    for offer in parse_offers(html):
        print(offer)
