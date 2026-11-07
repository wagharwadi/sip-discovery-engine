"""Reddit SIP posts + top comments.

Uses PRAW if REDDIT_CLIENT_ID/SECRET are in .env, otherwise Reddit's public .json endpoints.
Run: python collect/reddit.py
"""
import time
import requests
from common import save, env, UA

SUBS = ["IndiaInvestments", "mutualfunds", "personalfinanceindia", "IndianStreetBets"]
QUERIES = ["stop SIP", "pause SIP", "first SIP", "Groww SIP", "SIP loss", "SIP failed mandate",
           "stopped my SIP", "continue SIP"]
MAX_POSTS_WITH_COMMENTS = 120   # comments need one request per post
COMMENTS_PER_POST = 15

rows, seen = [], set()


def add(kind, pid, created, permalink, title, text):
    if pid in seen or not text or text in ("[deleted]", "[removed]"):
        return
    seen.add(pid)
    rows.append({"source": "reddit", "item_id": f"{kind}_{pid}",
                 "date": time.strftime("%Y-%m-%d", time.gmtime(created)) if created else "",
                 "url": f"https://www.reddit.com{permalink}", "rating": "",
                 "context": title, "text": text})


cid, sec = env("REDDIT_CLIENT_ID"), env("REDDIT_CLIENT_SECRET")
if cid and sec:
    import praw
    reddit = praw.Reddit(client_id=cid, client_secret=sec, user_agent=env("REDDIT_USER_AGENT", UA))
    posts = []
    for sub in SUBS:
        for q in QUERIES:
            for p in reddit.subreddit(sub).search(q, limit=50, sort="relevance", time_filter="all"):
                if p.id not in seen:
                    add("post", p.id, p.created_utc, p.permalink, p.title, f"{p.title}\n{p.selftext}".strip())
                    posts.append(p)
        print(f"  r/{sub}: {len(rows)} items", flush=True)
    for p in sorted(posts, key=lambda p: -p.num_comments)[:MAX_POSTS_WITH_COMMENTS]:
        p.comment_sort = "top"
        p.comments.replace_more(limit=0)
        for c in list(p.comments)[:COMMENTS_PER_POST]:
            add("comment", c.id, c.created_utc, c.permalink, p.title, c.body)
else:
    print("No Reddit keys -> using public .json endpoints")
    S = requests.Session()
    S.headers["User-Agent"] = UA

    def get(url, **params):
        for attempt in range(3):
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            time.sleep(2)  # stay well under the unauthenticated rate limit
            return r.json()
        raise RuntimeError(f"rate-limited: {url}")

    posts = []
    for sub in SUBS:
        for q in QUERIES:
            try:
                data = get(f"https://www.reddit.com/r/{sub}/search.json", q=q, restrict_sr=1,
                           sort="relevance", t="all", limit=100)
            except Exception as e:
                print(f"  r/{sub} '{q}' failed: {e}")
                continue
            for ch in data["data"]["children"]:
                d = ch["data"]
                if d["id"] not in seen:
                    add("post", d["id"], d.get("created_utc"), d["permalink"], d["title"],
                        f"{d['title']}\n{d.get('selftext', '')}".strip())
                    posts.append(d)
        print(f"  r/{sub}: {len(rows)} items", flush=True)

    top = sorted(posts, key=lambda d: -d.get("num_comments", 0))[:MAX_POSTS_WITH_COMMENTS]
    for i, d in enumerate(top, 1):
        try:
            data = get(f"https://www.reddit.com{d['permalink']}.json", sort="top", limit=COMMENTS_PER_POST, depth=1)
        except Exception as e:
            print(f"  comments for {d['id']} failed: {e}")
            continue
        for ch in data[1]["data"]["children"][:COMMENTS_PER_POST]:
            c = ch.get("data", {})
            if ch.get("kind") == "t1":
                add("comment", c["id"], c.get("created_utc"), c.get("permalink", d["permalink"]), d["title"], c.get("body", ""))
        if i % 20 == 0:
            print(f"  comments: {i}/{len(top)} posts, {len(rows)} items", flush=True)

save(rows, "reddit")
