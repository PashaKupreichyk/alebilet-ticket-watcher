"""
Simple JSON-file storage for filters and dedupe state.
Files live in the repo and get committed back by the GitHub Action after each run.
"""
import json
import os

FILTERS_PATH = "filters.json"
STATE_PATH = "state.json"


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_filters():
    return _load(FILTERS_PATH, [])


def save_filters(filters):
    _save(FILTERS_PATH, filters)


def load_state():
    return _load(STATE_PATH, {"telegram_offset": 0, "seen_ticket_ids": {}})


def save_state(state):
    _save(STATE_PATH, state)


def next_filter_id(filters):
    used = {f["id"] for f in filters}
    i = 1
    while i in used:
        i += 1
    return i
