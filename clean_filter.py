"""Step 3: combine raw CSVs -> dedupe -> strip PII -> drop short -> keep SIP-related.

Output:
  data/filtered_data.csv   (PII-stripped, safe to use in the app)
  data/source_counts.csv   (raw vs filtered per source, for the Evidence Log)
Run: python clean_filter.py
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

# ---------------------------------------------------------------- PII
PII = [
    (re.compile(r"https?://\S+|www\.\S+"), "[URL]"),
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)*"), "[EMAIL/UPI]"),      # emails and UPI ids
    (re.compile(r"(?<!\w)(\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\w)"), "[PHONE]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(r"\b\d{9,18}\b"), "[NUMBER]"),                       # account / folio / order numbers
    (re.compile(r"(?<![\w/])/?u/[\w-]+", re.I), "[USER]"),
    (re.compile(r"(?<!\w)@[\w.]{2,}"), "[USER]"),
]


def strip_pii(t: str) -> str:
    for rx, rep in PII:
        t = rx.sub(rep, t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- relevance
# Strong: the text itself is about SIP / MF continuation.
STRONG = re.compile(
    r"\bsips?\b|systematic investment|mutual ?funds?|\bmfs?\b|mandate|auto ?pay|auto[- ]?debit|\bnach\b|"
    r"instal+ments?|\bnav\b|\bxirr\b|redeem|redemption|step[- ]?up|एसआईपी|सिप|म्यूचुअल",
    re.I)
# Weak: continuation words. Count only when the thread/video title (context) is about SIP.
WEAK = re.compile(
    r"\b(stop+(ed|ping)?|pause[ds]?|continu\w*|cancel+\w*|loss|losing|negative|red|returns?|profit|"
    r"invest\w*|salary|income|job|money|withdraw\w*|month(s|ly)?|market|crash|fall|debit|bank|"
    r"band|ruk|nuksan|paisa)\b",
    re.I)
MIN_CHARS, MIN_WORDS = 30, 6


def is_relevant(text: str, context: str) -> bool:
    if STRONG.search(text):
        return True
    return bool(STRONG.search(context or "")) and bool(WEAK.search(text))


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9ऀ-ॿ]+", "", t.lower())


# ---------------------------------------------------------------- run
frames = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in sorted(RAW.glob("*.csv"))]
df = pd.concat(frames, ignore_index=True)
counts = df.groupby("source").size().rename("raw").to_frame()

df["text"] = df["text"].map(strip_pii)
df["context"] = df["context"].map(strip_pii)
df = df[df["text"].str.len() > 0]

df["_n"] = df["text"].map(norm)
df = df.drop_duplicates("_n")
counts["after_dedupe"] = df.groupby("source").size()

df = df[(df["text"].str.len() >= MIN_CHARS) & (df["text"].str.split().str.len() >= MIN_WORDS)]
counts["after_length"] = df.groupby("source").size()

df = df[[is_relevant(t, c) for t, c in zip(df["text"], df["context"])]]
counts["sip_relevant"] = df.groupby("source").size()

df = df.drop(columns="_n").reset_index(drop=True)
df.insert(0, "uid", [f"{s[:2]}_{i:05d}" for i, s in enumerate(df["source"])])
df.to_csv(OUT / "filtered_data.csv", index=False, encoding="utf-8")

counts = counts.fillna(0).astype(int)
counts.loc["TOTAL"] = counts.sum()
counts.to_csv(OUT / "source_counts.csv")
print(counts.to_string())
print(f"\nSaved {len(df)} rows -> data/filtered_data.csv")
