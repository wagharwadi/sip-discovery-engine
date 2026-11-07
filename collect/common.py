"""Shared helpers for all collectors. Every collector saves the SAME columns.

We never save usernames / author names (PII by design).
"""
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

COLUMNS = ["source", "item_id", "date", "url", "rating", "context", "text"]

UA = "sip-research-script/0.1 (student research project)"


def save(rows, name):
    """Write rows (list of dicts) to data/raw/<name>.csv. Returns the path."""
    path = RAW / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in COLUMNS})
    print(f"[{name}] saved {len(rows)} rows -> {path.relative_to(ROOT)}")
    return path


def env(key, default=None):
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    return os.getenv(key, default)
