"""Groww App Store (India) reviews via Apple's public RSS feed (max ~500). Run: python collect/app_store.py"""
import time
import requests
from common import save, UA

H = {"User-Agent": UA}

# find the app id instead of hard-coding it
res = requests.get("https://itunes.apple.com/search",
                   params={"term": "groww", "country": "in", "entity": "software", "limit": 5},
                   headers=H, timeout=30).json()["results"]
app = next(a for a in res if "groww" in a["trackName"].lower())
app_id = app["trackId"]
print(f"App: {app['trackName']} ({app_id})")

rows = []
for sort in ("mostrecent", "mosthelpful"):
    for page in range(1, 11):
        url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_id}/sortby={sort}/json"
        r = requests.get(url, headers=H, timeout=30)
        if r.status_code != 200:
            break
        entries = r.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        entries = [e for e in entries if "im:rating" in e]  # first entry can be app info
        if not entries:
            break
        for e in entries:
            rows.append({
                "source": "app_store", "item_id": e["id"]["label"],
                "date": e.get("updated", {}).get("label", "")[:10],
                "url": f"https://apps.apple.com/in/app/id{app_id}",
                "rating": e["im:rating"]["label"],
                "context": e.get("title", {}).get("label", ""),
                "text": e.get("content", {}).get("label", ""),
            })
        print(f"  {sort} page {page}: {len(rows)} total", flush=True)
        time.sleep(0.5)

# dedupe (same review can appear in both sorts)
uniq = {r["item_id"]: r for r in rows}
save(list(uniq.values()), "app_store")
