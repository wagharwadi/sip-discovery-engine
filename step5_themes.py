"""Step 5b: theme discovery, with a human review step in the middle.

  python step5_themes.py propose   -> AI proposes themes from the unmet needs
                                      saves data/themes_ai_v1.json (never edited) and data/themes.json (YOU edit)
  (you)  edit data/themes.json      -> merge / rename / split / fix themes, and write down each change
                                      in evidence_log.md section 5 (Evidence Log needs 2-3)
  python step5_themes.py assign    -> assigns every relevant item to one theme from data/themes.json
                                      saves data/theme_assignments.csv
"""
import json
import random
import sys
from pathlib import Path

import pandas as pd

from step5_extract import load_all_tagged

import taxonomy as T
from llm import ask_json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SYSTEM = "You are a senior user-research analyst. Output JSON only."


def load_tagged():
    rows = load_all_tagged()
    t = pd.DataFrame(rows).drop_duplicates("uid", keep="last")
    return t[t.is_relevant]


def propose():
    t = load_tagged()
    t = t[t.unmet_need.str.len() > 0]
    random.seed(7)
    lines = [f"[{r.trigger}|{r.action}] {r.unmet_need}" for r in t.itertuples()]
    sample = random.sample(lines, min(450, len(lines)))
    nodes = "\n".join(f"  {k}: {v}" for k, v in T.NODES.items())
    prompt = f"""Below are {len(sample)} "unmet needs" extracted from comments by Indian SIP / mutual fund investors
(format: [trigger|action] unmet need). Group them into 10-14 distinct THEMES of unmet need.

Rules:
- Themes must be specific and actionable for a product team (not "bad app").
- Keep "confused by return numbers" separate from "disappointed by returns".
- Keep involuntary payment/mandate problems separate from choosing to stop.
- Include one theme "other" for leftovers.
- For each theme give a decomposition node from:
{nodes}
- addressability (1-3): can Groww fix this WITHOUT giving investment advice or using fear/urgency? 3 = yes, clearly.
  Give a one-line reason.

Return {{"themes": [{{"id": "short_snake_case", "name": "...", "definition": "one sentence",
"node": "A|B|C|D|E|X", "addressability": 1-3, "addressability_reason": "...",
"example_needs": ["...", "..."]}}]}}

NEEDS:
""" + "\n".join(sample)
    res, provider = ask_json(prompt, system=SYSTEM, quality=True, temperature=0.2)
    themes = res["themes"]
    out = {"proposed_by": provider, "based_on_needs": len(sample), "themes": themes}
    (DATA / "themes_ai_v1.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    edit = DATA / "themes.json"
    if not edit.exists():
        edit.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(themes)} themes proposed via {provider}:")
    for th in themes:
        print(f"  [{th['node']}] {th['id']}: {th['name']} (addr {th['addressability']})")
    print("\nNow review data/themes.json and log changes in evidence_log.md section 5, then run: assign")


def assign():
    themes = json.loads((DATA / "themes.json").read_text(encoding="utf-8"))["themes"]
    ids = {th["id"] for th in themes}
    fallback = "other" if "other" in ids else themes[-1]["id"]
    menu = "\n".join(f"- {th['id']}: {th['name']} - {th['definition']}" for th in themes)
    t = load_tagged()
    # relevant but no signal (no unmet need AND no trigger, e.g. "great app for SIP"): don't force into a theme
    signal = (t.unmet_need.str.strip().str.len() > 0) | (t.trigger != "none")
    no_sig = t[~signal]
    t = t[signal]
    out_path = DATA / "theme_assignments.csv"
    done = pd.read_csv(out_path) if out_path.exists() else pd.DataFrame(columns=["uid", "theme"])
    done = done[done.theme.isin(ids) & done.uid.isin(t.uid)]  # re-assign if a theme id was removed/renamed
    todo = t[~t.uid.isin(done.uid)]
    print(f"{len(no_sig)} relevant items have no signal (theme = no_signal); {len(todo)} items to assign")
    rows = done.to_dict("records") + [{"uid": u, "theme": "no_signal"} for u in no_sig.uid]
    for i in range(0, len(todo), 60):
        chunk = todo.iloc[i:i + 60]
        items = [{"uid": r.uid, "trigger": r.trigger, "action": r.action, "unmet_need": r.unmet_need,
                  "quote": r.evidence_quote} for r in chunk.itertuples()]
        prompt = (f"Assign each item to exactly ONE theme id.\nTHEMES:\n{menu}\n\n"
                  f'Return {{"items": [{{"uid": ..., "theme": ...}}]}}\n\nITEMS:\n{json.dumps(items, ensure_ascii=False)}')
        try:
            res, provider = ask_json(prompt, system=SYSTEM)
        except Exception as e:
            print(f"  chunk {i // 60 + 1} failed: {str(e)[:150]} (re-run assign to retry)")
            continue
        got = {str(x.get("uid")): x.get("theme") for x in res.get("items", [])}
        for r in chunk.itertuples():
            if r.uid in got:
                rows.append({"uid": r.uid, "theme": got[r.uid] if got[r.uid] in ids else fallback})
        pd.DataFrame(rows).to_csv(out_path, index=False)
        print(f"  chunk {i // 60 + 1}: {len(got)} assigned via {provider}", flush=True)
    a = pd.DataFrame(rows)
    print(a.theme.value_counts().to_string())


if __name__ == "__main__":
    {"propose": propose, "assign": assign}[sys.argv[1] if len(sys.argv) > 1 else "propose"]()
