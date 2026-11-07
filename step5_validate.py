"""Step 5d: compare AI labels with YOUR hand labels in data/golden_set.xlsx.

Run only AFTER you've finished labelling. Output: data/golden_agreement.csv + step5_validation.md
Run: python step5_validate.py
"""
import json
from pathlib import Path

import pandas as pd

from step5_extract import load_all_tagged

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FIELDS = ["is_relevant", "lifecycle_stage", "action", "trigger"]
SEGMENTS = ["age_band", "income_type", "source_of_money", "influencer"]

gs = pd.read_excel(DATA / "golden_set.xlsx", sheet_name="golden_set", dtype=str).fillna("")
gs = gs[gs.is_relevant.str.strip() != ""]
if gs.empty:
    raise SystemExit("Golden set has no labels yet. Fill data/golden_set.xlsx first.")

ai = pd.DataFrame(load_all_tagged())
ai = ai.drop_duplicates("uid", keep="last").set_index("uid")
ai["is_relevant"] = ai.is_relevant.map({True: "yes", False: "no"})

rows = []
for r in gs.itertuples():
    if r.uid not in ai.index:
        continue
    a = ai.loc[r.uid]
    human_rel = r.is_relevant.strip().lower()
    row = {"uid": r.uid, "source": r.source}
    for f in FIELDS:
        h = str(getattr(r, f)).strip().lower() or ("unknown" if f != "is_relevant" else "")
        row[f"human_{f}"], row[f"ai_{f}"] = h, str(a[f])
        # tags only compared when the human said the item is relevant
        row[f"match_{f}"] = (h == str(a[f])) if (f == "is_relevant" or human_rel == "yes") else None
    # invented segment info: AI filled a value the human left as unknown
    row["ai_invented_segment"] = any(
        str(a[s]) != "unknown" and (str(getattr(r, s)).strip().lower() or "unknown") == "unknown" for s in SEGMENTS)
    row["ai_quote"] = a["evidence_quote"]
    rows.append(row)

res = pd.DataFrame(rows)
res.to_csv(DATA / "golden_agreement.csv", index=False)

md = [f"# Step 5 validation: AI vs hand-labelled golden set\n", f"Items compared: **{len(res)}**\n",
      "| Field | Agreement |", "|---|---|"]
for f in FIELDS:
    m = res[f"match_{f}"].dropna()
    md.append(f"| {f} | **{100 * m.mean():.0f}%** ({int(m.sum())}/{len(m)}) |")
md.append(f"| segment invented by AI | {int(res.ai_invented_segment.sum())} of {len(res)} items |")
md += ["\n## Disagreements (failure cases)\n", "| uid | field | human | AI |", "|---|---|---|---|"]
for r in res.itertuples():
    for f in FIELDS:
        if getattr(r, f"match_{f}") is False:
            md.append(f"| {r.uid} | {f} | {getattr(r, f'human_{f}')} | {getattr(r, f'ai_{f}')} |")
trig = res.dropna(subset=["match_trigger"])
trig = trig[~trig.match_trigger.astype(bool)]
if len(trig):
    md += ["\n## Trigger confusion (human → AI)\n"]
    for (h, a), n in trig.groupby(["human_trigger", "ai_trigger"]).size().sort_values(ascending=False).items():
        md.append(f"- {h} → {a}: {n}")
(ROOT / "step5_validation.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
