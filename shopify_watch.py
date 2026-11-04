#!/usr/bin/env python3
"""
Shopify internship watcher (cloud version, runs in GitHub Actions).
Checks Shopify's careers pages every 60s and pushes an urgent ntfy notification
(plus optional email) when a new internship posting appears.

Config via environment variables (set as GitHub repo secrets):
  NTFY_TOPIC   required  - your ntfy topic name
  ALERT_EMAIL  optional  - also email alerts here (ntfy forwards it)
  RUN_SECONDS  optional  - how long to keep looping before exiting (default 20700 = 5h45m)
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "").strip()
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "20700"))
INTERVAL_SECONDS = 60

URLS = [
    "https://www.shopify.com/careers",
    "https://www.shopify.com/careers?keywords=intern",
    "https://www.shopify.com/careers/search?keywords=intern",
    "https://internships.shopify.com/",
]

STATE_FILE = Path(__file__).with_name("state.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36"

ROLE_LINK = re.compile(r'href="((?:https://www\.shopify\.com)?/careers/[a-z0-9\-]+_[0-9a-f\-]{36})"', re.I)
INTERN_WORDS = re.compile(r"intern", re.I)
INTERN_PAGE_HINTS = re.compile(
    r"(apply now|applications (are )?(now )?open|20\d\d[^<]{0,40}(summer|fall|winter))", re.I
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def notify(title, msg, click=None, urgent=True):
    headers = {"Title": title, "Priority": "urgent" if urgent else "default", "Tags": "rotating_light"}
    if click:
        headers["Click"] = click
    if ALERT_EMAIL and urgent:
        headers["Email"] = ALERT_EMAIL
    req = urllib.request.Request(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode(), headers=headers)
    for attempt in range(3):
        try:
            urllib.request.urlopen(req, timeout=15)
            return
        except Exception as e:
            print(f"[notify failed, attempt {attempt + 1}] {e}", file=sys.stderr)
            time.sleep(5)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"links": [], "intern_page_hash": None, "initialized": False}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2) + "\n")


def check(state):
    found_links = set()
    snippet = None

    for url in URLS:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[fetch failed] {url}: {e}", file=sys.stderr)
            continue
        for m in ROLE_LINK.finditer(html):
            link = m.group(1)
            if link.startswith("/"):
                link = "https://www.shopify.com" + link
            if INTERN_WORDS.search(link):
                found_links.add(link)
        if "internships.shopify.com" in url:
            hints = sorted(set(h.group(0).strip().lower() for h in INTERN_PAGE_HINTS.finditer(html)))
            snippet = "|".join(hints)

    seen = set(state["links"])
    new_links = sorted(found_links - seen)

    if state["initialized"]:
        for link in new_links:
            print(f"NEW POSTING: {link}")
            notify("Shopify internship posted", link, click=link)
        if snippet is not None:
            h = hashlib.sha256(snippet.encode()).hexdigest()
            if state["intern_page_hash"] and h != state["intern_page_hash"]:
                print(f"internships.shopify.com changed: {snippet}")
                notify("Shopify internships page changed", snippet[:180] or "check now",
                       click="https://internships.shopify.com/")
    else:
        print(f"Baseline: {len(found_links)} existing intern links (no alerts for these).")
        for l in sorted(found_links):
            print("  ", l)
        notify("Shopify watcher running",
               f"Baseline: {len(found_links)} existing intern postings. You'll get an urgent alert on new ones.",
               urgent=False)

    state["links"] = sorted(seen | found_links)
    if snippet is not None:
        state["intern_page_hash"] = hashlib.sha256(snippet.encode()).hexdigest()
    state["initialized"] = True
    save_state(state)


def main():
    if not NTFY_TOPIC:
        sys.exit("NTFY_TOPIC is not set.")
    state = load_state()
    deadline = time.time() + RUN_SECONDS
    while time.time() < deadline:
        try:
            check(state)
        except Exception as e:
            print(f"[check error] {e}", file=sys.stderr)
        print(time.strftime("%H:%M:%S"), "checked", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
