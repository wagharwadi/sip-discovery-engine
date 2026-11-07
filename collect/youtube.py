"""YouTube comments on popular SIP videos (Hindi + English). Run: python collect/youtube.py

Quota: each search = 100 units, each comment page = 1 unit (free daily quota = 10,000).
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from common import save, env

QUERIES = ["SIP for beginners India", "should I stop my SIP", "SIP stop karna chahiye",
           "SIP in loss what to do", "Groww SIP tutorial"]
VIDEOS_PER_QUERY = 4
MAX_VIDEOS = 15
PAGES_PER_VIDEO = 3  # 100 comments per page

yt = build("youtube", "v3", developerKey=env("YOUTUBE_API_KEY"))

videos = {}
for q in QUERIES:
    res = yt.search().list(q=q, part="snippet", type="video", maxResults=VIDEOS_PER_QUERY,
                           regionCode="IN", relevanceLanguage="en", order="relevance").execute()
    for it in res["items"]:
        videos.setdefault(it["id"]["videoId"], it["snippet"]["title"])
videos = dict(list(videos.items())[:MAX_VIDEOS])
print(f"{len(videos)} videos")

rows = []
for vid, title in videos.items():
    token, n = None, 0
    for _ in range(PAGES_PER_VIDEO):
        try:
            res = yt.commentThreads().list(videoId=vid, part="snippet", maxResults=100, order="relevance",
                                           textFormat="plainText", pageToken=token).execute()
        except HttpError as e:  # comments disabled etc.
            print(f"  skip {vid}: {e.status_code}")
            break
        for it in res["items"]:
            s = it["snippet"]["topLevelComment"]["snippet"]
            rows.append({"source": "youtube", "item_id": it["id"], "date": s["publishedAt"][:10],
                         "url": f"https://www.youtube.com/watch?v={vid}", "rating": "",
                         "context": title, "text": s.get("textOriginal") or s.get("textDisplay", "")})
            n += 1
        token = res.get("nextPageToken")
        if not token:
            break
    print(f"  {n:4d} comments  {title[:60]}", flush=True)

save(rows, "youtube")
