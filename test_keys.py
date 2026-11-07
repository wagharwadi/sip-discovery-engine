"""Step 1 check: confirms every free API key / data source works.
Run:  python test_keys.py
"""
import os
from dotenv import load_dotenv

load_dotenv()
results = []


def report(name, ok, msg=""):
    results.append(ok)
    print(f"{'✅' if ok else '❌'} {name}" + (f" - {msg}" if msg else ""))


# 1. Gemini
try:
    from google import genai
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY missing in .env")
    client = genai.Client(api_key=key)
    names_cache = None
    for var, default in [("GEMINI_MODEL", "gemini-3.5-flash-lite"), ("GEMINI_QUALITY_MODEL", "gemini-3.5-flash")]:
        model = os.getenv(var, default)
        try:
            r = client.models.generate_content(model=model, contents="Reply with just: OK")
            report(f"Gemini ({var})", True, f"{model} replied: {r.text.strip()[:20]}")
        except Exception as e:
            if names_cache is None:
                names_cache = [m.name for m in client.models.list() if "flash" in m.name][:8]
            report(f"Gemini ({var})", False, f"model '{model}' failed ({e}). Try one of these: {names_cache}")
except Exception as e:
    report("Gemini", False, str(e))

# 2. Groq
try:
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY missing in .env")
    client = Groq(api_key=key)
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    try:
        # reasoning models spend tokens "thinking" first, so allow enough for a visible reply
        r = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "Reply with just: OK"}], max_tokens=300
        )
        report("Groq", True, f"{model} replied: {r.choices[0].message.content.strip()}")
    except Exception as e:
        names = [m.id for m in client.models.list().data][:8]
        report("Groq", False, f"model '{model}' failed ({e}). Try one of these in GROQ_MODEL: {names}")
except Exception as e:
    report("Groq", False, str(e))

# 3. YouTube Data API
try:
    from googleapiclient.discovery import build
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise ValueError("YOUTUBE_API_KEY missing in .env")
    yt = build("youtube", "v3", developerKey=key)
    r = yt.search().list(q="SIP for beginners India", part="snippet", type="video", maxResults=1).execute()
    report("YouTube", True, f"found: {r['items'][0]['snippet']['title'][:50]}")
except Exception as e:
    report("YouTube", False, f"{e}  (check the API is ENABLED in Google Cloud)")

# 4. Google Play (no key needed)
try:
    from google_play_scraper import reviews, Sort
    revs, _ = reviews("com.nextbillion.groww", lang="en", country="in", sort=Sort.NEWEST, count=3)
    report("Google Play", len(revs) > 0, f"fetched {len(revs)} Groww reviews")
except Exception as e:
    report("Google Play", False, str(e))

# 5. Reddit (optional)
try:
    import praw
    cid, sec = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
    if not cid or not sec:
        print("⚪ Reddit - skipped (no keys). Optional; we have a fallback.")
    else:
        reddit = praw.Reddit(client_id=cid, client_secret=sec,
                             user_agent=os.getenv("REDDIT_USER_AGENT", "sip-research-script/0.1"))
        post = next(reddit.subreddit("mutualfunds").search("SIP stop", limit=1))
        report("Reddit", True, f"found: {post.title[:50]}")
except Exception as e:
    report("Reddit", False, f"{e}  (optional; skip if blocked)")

print("\nAll required checks passed 🎉" if all(results) else "\nFix the ❌ lines (send me the message if stuck).")
