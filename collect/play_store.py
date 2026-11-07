"""Groww Play Store reviews: newest + most relevant (deduped). Run: python collect/play_store.py [count_per_sort]"""
import sys
import time
from google_play_scraper import reviews, Sort
from common import save

APP = "com.nextbillion.groww"
PER_SORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

rows, seen = [], set()
for sort in (Sort.NEWEST, Sort.MOST_RELEVANT):
    token, got = None, 0
    while got < PER_SORT:
        batch, token = reviews(APP, lang="en", country="in", sort=sort,
                               count=min(200, PER_SORT - got), continuation_token=token)
        if not batch:
            break
        got += len(batch)
        for r in batch:
            if r["reviewId"] in seen:
                continue
            seen.add(r["reviewId"])
            rows.append({
                "source": "play_store", "item_id": r["reviewId"],
                "date": r["at"].date().isoformat() if r.get("at") else "",
                "url": f"https://play.google.com/store/apps/details?id={APP}",
                "rating": r.get("score"), "context": "", "text": r.get("content") or "",
            })
        print(f"  {sort.name}: {got}", flush=True)
        if token is None or token.token is None:
            break
        time.sleep(0.3)

save(rows, "play_store")
