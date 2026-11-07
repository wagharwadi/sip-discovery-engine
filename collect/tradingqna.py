"""TradingQ&A (Discourse forum) SIP threads: search, then read each topic's posts.
Run: python collect/tradingqna.py
"""
import html
import re
import time
import requests
from common import save, UA

BASE = "https://tradingqna.com"
QUERIES = ["stop sip", "pause sip", "sip mandate", "sip failed", "first sip", "sip loss",
           "continue sip", "sip cancel", "sip groww"]
MAX_TOPICS = 200
POSTS_PER_TOPIC = 20

S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "application/json"})


def get(path, **params):
    for attempt in range(3):
        r = S.get(BASE + path, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        time.sleep(0.7)
        return r.json()
    raise RuntimeError("rate-limited")


def strip_html(s):
    s = re.sub(r"<aside[^>]*class=\"[^\"]*quote.*?</aside>", " ", s or "", flags=re.S)  # quoted posts carry usernames
    s = re.sub(r"<a[^>]*class=\"mention\"[^>]*>.*?</a>", "[USER]", s, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


topics = {}
for q in QUERIES:
    for page in (1, 2):
        try:
            data = get("/search.json", q=q, page=page)
        except Exception as e:
            print(f"  search '{q}' p{page} failed: {e}")
            break
        for t in data.get("topics", []):
            topics.setdefault(t["id"], t)
        if not data.get("topics"):
            break
    print(f"  '{q}': {len(topics)} topics so far", flush=True)

rows = []
for i, (tid, t) in enumerate(list(topics.items())[:MAX_TOPICS], 1):
    try:
        data = get(f"/t/{tid}.json")
    except Exception as e:
        print(f"  topic {tid} failed: {e}")
        continue
    for p in data["post_stream"]["posts"][:POSTS_PER_TOPIC]:
        rows.append({"source": "tradingqna", "item_id": f"{tid}_{p['post_number']}",
                     "date": p["created_at"][:10], "url": f"{BASE}/t/{t.get('slug', 'x')}/{tid}/{p['post_number']}",
                     "rating": "", "context": t.get("title", ""), "text": strip_html(p.get("cooked"))})
    if i % 25 == 0:
        print(f"  read {i} topics, {len(rows)} posts", flush=True)

save(rows, "tradingqna")
