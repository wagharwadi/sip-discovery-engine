"""Step 5a: structured extraction. Tags every item in data/filtered_data.csv with the taxonomy.

- Batches of 20, saves after EVERY batch to data/tagged.jsonl (safe to stop and re-run: it resumes).
- Golden-set items go first, so validation can run early.
- Every value is checked against taxonomy.py; bad values are fixed to unknown/other and logged.
- evidence_quote is checked against the original text (catches invented quotes).

Run: python step5_extract.py [max_batches] [shard] [n_shards]
     (parallel: run shards 0..n-1 at once; each writes data/tagged_<shard>.jsonl)
"""
import json
import sys
from pathlib import Path

import pandas as pd

import taxonomy as T
from llm import ask_json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = DATA / "tagged.jsonl"
ISSUES = DATA / "logs" / "extract_issues.jsonl"
BATCH = 20
MAX_CHARS = 1200
PROMPT_VERSION = "extract_v1"

SYSTEM = ("You are a careful user-research analyst. You tag public comments about SIPs (systematic "
          "investment plans) in Indian mutual funds, mostly about the Groww app. Comments may be in "
          "English, Hindi or Hinglish. You never invent facts that are not in the text. Output JSON only.")

INSTRUCTIONS = """Tag each item below. Use ONLY these allowed values:

{taxonomy}

Other fields:
- is_relevant: true if the item is about the experience of starting, continuing, pausing, reducing, stopping,
  restarting or paying for a SIP, or about being a first-time mutual fund investor. false for stocks/IPO/F&O-only,
  KYC-only, generic app praise with no SIP/MF experience, or spam. If false, set the other tags to unknown/none/"".
- what_they_check: what numbers/screens they look at (e.g. "returns %", "XIRR", "current value"), or "".
- outside_app_behaviour: one of youtube, friends_family, reddit_forum, advisor_ca, other, none.
- emotion: one of anxious, frustrated, confused, disappointed, angry, hopeful, confident, neutral.
- unmet_need: what the person needed and did not get, in plain English, max 15 words. "" if none.
- evidence_quote: copy an EXACT span (max 20 words) from the text that supports the trigger. Do not translate.
- confidence: 0.0 to 1.0, how sure you are about action + trigger.

Return a JSON object: {{"items": [ {{"uid": ..., "is_relevant": ..., "lifecycle_stage": ..., "action": ...,
"trigger": ..., "what_they_check": ..., "outside_app_behaviour": ..., "emotion": ..., "unmet_need": ...,
"segment_signals": {{"age_band": ..., "income_type": ..., "source_of_money": ..., "influencer": ...}},
"evidence_quote": ..., "confidence": ...}} ]}}
One entry per input item, same uid, same order.

ITEMS:
{items}"""

OUTSIDE = {"youtube", "friends_family", "reddit_forum", "advisor_ca", "other", "none"}
EMOTIONS = {"anxious", "frustrated", "confused", "disappointed", "angry", "hopeful", "confident", "neutral"}

# Near-miss values the model actually produced (from data/logs/extract_issues.jsonl) -> the allowed value
# they mean. Mostly a valid tag from the wrong field, or the other field's spelling.
SYNONYMS = {
    "action": {"fund_switch": "restarted", "switched": "restarted", "setup_friction": "setup_failed",
               "payment_failure": "lapsed_involuntary"},
    "trigger": {"lapsed_involuntary": "payment_failure", "mandate_failure": "payment_failure"},
    "outside_app_behaviour": {"youtube_social": "youtube", "friend_family": "friends_family"},
    "influencer": {"youtube": "youtube_social", "friends_family": "friend_family", "friends": "friend_family"},
    "emotion": {"concerned": "anxious", "worried": "anxious", "curious": "neutral", "skeptical": "neutral"},
}


def normalise(key: str, v: str) -> str:
    v = SYNONYMS.get(key, {}).get(v, v)
    if key == "age_band" and v.isdigit():  # e.g. "31" -> "28-35"
        a = int(v)
        v = "<21" if a < 21 else "21-27" if a <= 27 else "28-35" if a <= 35 else "36+"
    return v


def load_all_tagged():
    """All tagged records from data/tagged*.jsonl (single run or parallel shards)."""
    rows = []
    for p in sorted(DATA.glob("tagged*.jsonl")):
        rows += [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
    return rows


def clean(rec: dict, src: dict) -> tuple[dict, list[str]]:
    """Force every field into the allowed values. Returns (record, list of fixes)."""
    fixes = []

    def pick(key, allowed, default):
        v = normalise(key, str(rec.get(key, default)).strip().lower())
        if v not in allowed:
            fixes.append(f"{key}={v!r}->{default}")
            v = default
        return v

    seg_in = rec.get("segment_signals") or {}
    out = {
        "uid": src["uid"],
        "is_relevant": str(rec.get("is_relevant")).lower() in ("true", "1", "yes"),
        "lifecycle_stage": pick("lifecycle_stage", T.LIFECYCLE_STAGES, "unknown"),
        "action": pick("action", T.ACTIONS, "unknown"),
        "trigger": pick("trigger", T.TRIGGERS, "other"),
        "what_they_check": str(rec.get("what_they_check") or "")[:100],
        "outside_app_behaviour": pick("outside_app_behaviour", OUTSIDE, "none"),
        "emotion": pick("emotion", EMOTIONS, "neutral"),
        "unmet_need": str(rec.get("unmet_need") or "")[:150],
        "evidence_quote": str(rec.get("evidence_quote") or "")[:250],
    }
    for k, allowed in T.SEGMENT_SIGNALS.items():
        v = normalise(k, str(seg_in.get(k, "unknown")).strip().lower())
        if v not in allowed:
            fixes.append(f"{k}={v!r}->unknown")
            v = "unknown"
        out[k] = v
    try:
        out["confidence"] = max(0.0, min(1.0, float(rec.get("confidence", 0.5))))
    except (TypeError, ValueError):
        out["confidence"] = 0.5
    q = out["evidence_quote"].strip().strip('"').lower()
    out["quote_ok"] = (not q) or (q in src["text"].lower())  # False = model invented/edited the quote
    out["node"] = T.node_for(out["trigger"]) if out["is_relevant"] else "X"
    return out, fixes


def repair():
    """Re-apply SYNONYMS to already-saved records, using the original values kept in the issues log."""
    import ast
    orig = {}  # uid -> {field: original value}
    for l in ISSUES.open(encoding="utf-8"):
        d = json.loads(l)
        for fx in d.get("fixes", []):
            field, rest = fx.split("=", 1)
            orig.setdefault(d["uid"], {})[field] = ast.literal_eval(rest.rsplit("->", 1)[0])
    allowed = {"lifecycle_stage": T.LIFECYCLE_STAGES, "action": T.ACTIONS, "trigger": T.TRIGGERS,
               "outside_app_behaviour": OUTSIDE, "emotion": EMOTIONS, **T.SEGMENT_SIGNALS}
    changed = []
    for p in sorted(DATA.glob("tagged*.jsonl")):
        recs = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
        for r in recs:
            for field, old in orig.get(r["uid"], {}).items():
                new = normalise(field, old)
                if new in allowed[field] and r.get(field) != new:
                    changed.append((r["uid"], field, old, r.get(field), new))
                    r[field] = new
            if r["is_relevant"]:
                r["node"] = T.node_for(r["trigger"])
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    for c in changed:
        print(f"  {c[0]}: {c[1]} {c[2]!r} (was saved as {c[3]!r}) -> {c[4]!r}")
    print(f"repaired {len(changed)} values")


def main(max_batches=None, shard=0, n_shards=1):
    df = pd.read_csv(DATA / "filtered_data.csv", dtype=str, keep_default_na=False)
    gs_path = DATA / "golden_set.xlsx"
    if gs_path.exists():  # golden set first
        gs = set(pd.read_excel(gs_path, sheet_name="golden_set").uid)
        df = pd.concat([df[df.uid.isin(gs)], df[~df.uid.isin(gs)]])

    done = set()
    for p in DATA.glob("tagged*.jsonl"):
        done |= {json.loads(l)["uid"] for l in p.open(encoding="utf-8") if l.strip()}
    todo = df[~df.uid.isin(done)]
    todo = todo.iloc[shard::n_shards]
    out = OUT if n_shards == 1 else DATA / f"tagged_{shard}.jsonl"
    print(f"{len(done)} already tagged, {len(todo)} to go ({-(-len(todo) // BATCH)} batches)", flush=True)

    tax = T.prompt_block()
    for b, start in enumerate(range(0, len(todo), BATCH), 1):
        if max_batches and b > max_batches:
            break
        chunk = todo.iloc[start:start + BATCH]
        items = [{"uid": r.uid, "source": r.source, "title_or_context": r.context[:150], "text": r.text[:MAX_CHARS]}
                 for r in chunk.itertuples()]
        prompt = INSTRUCTIONS.format(taxonomy=tax, items=json.dumps(items, ensure_ascii=False))
        try:
            res, provider = ask_json(prompt, system=SYSTEM)
        except Exception as e:
            print(f"  batch {b}: FAILED ({str(e)[:200]}) - will retry on next run", flush=True)
            continue
        got = {str(x.get("uid")): x for x in res.get("items", []) if isinstance(x, dict)}
        by_uid = {r["uid"]: r for r in items}
        with out.open("a", encoding="utf-8") as f, ISSUES.open("a", encoding="utf-8") as fi:
            for uid, src in by_uid.items():
                if uid not in got:
                    fi.write(json.dumps({"uid": uid, "issue": "missing from model output"}) + "\n")
                    continue
                rec, fixes = clean(got[uid], src)
                rec.update(provider=provider, prompt_version=PROMPT_VERSION)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if fixes or not rec["quote_ok"]:
                    fi.write(json.dumps({"uid": uid, "fixes": fixes, "quote_ok": rec["quote_ok"]}) + "\n")
        print(f"  [{shard}] batch {b}: {len(got)}/{len(items)} tagged via {provider}", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["repair"]:
        repair()
        sys.exit()
    a = sys.argv[1:] + [None] * 3
    main(int(a[0]) if a[0] and a[0] != "0" else None, int(a[1] or 0), int(a[2] or 1))
