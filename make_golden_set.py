"""Step 4: pick ~20 items for hand-labelling, BEFORE any AI tagging.

Picking uses only keyword rules (no AI), so the golden set stays independent of the engine.
Output: data/golden_set.xlsx (labels are blank, with dropdowns from taxonomy.py)
Run: python make_golden_set.py
"""
import re
import warnings
warnings.filterwarnings("ignore", "This pattern")
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

import taxonomy as T

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "data" / "filtered_data.csv", dtype=str, keep_default_na=False)
df = df[df.text.str.len().between(60, 700)]  # readable length for labelling

# bucket -> (regex, how many). Ordered: rarer/harder buckets pick first.
BUCKETS = [
    ("payment / mandate failure", r"mandate|auto ?pay|debit|bounce|rejected|insufficient|failed", 3),
    ("stop / pause / reduce",     r"\b(stop+ed|stopping|paus|cancel|reduce|band kar|kam kr|kam kar)", 3),
    ("returns / loss",            r"\b(loss|negative|red|returns?|crash|fall|nuksan)\b", 3),
    ("confusing numbers",         r"\bxirr\b|\bnav\b|absolute return|cagr|current value", 2),
    ("money need / income",       r"salary|job|emergency|withdraw|need (the )?money|income|paisa", 2),
    ("peer / influencer",         r"friend|youtube|video|advisor|family|colleague|told me", 2),
    ("setup / first SIP",         r"first sip|start(ed|ing)? (a |my )?sip|new to|beginner", 2),
    ("continued through doubt",   r"continu|stay invested|didn'?t stop|keep going|still investing", 2),
    ("HARD: Hinglish",            r"\b(hai|kya|mai|nahi|karna|kaise|hoga|krna|mera)\b", 2),
    ("HARD: app bug + SIP mixed", r"(bug|crash|glitch|support|customer care|worst app).*\bsip\b|\bsip\b.*(bug|glitch|support|customer care|worst app)", 1),
    ("DISTRACTOR: probably off-topic", None, 2),
]
SIP = r"\bsips?\b|एसआईपी|सिप"  # every non-distractor pick must mention SIP
# keep a source mix: max per source
SOURCE_CAP = {"play_store": 11, "youtube": 6, "tradingqna": 5, "app_store": 2}

picked, used = [], set()
src_n = {s: 0 for s in SOURCE_CAP}
for name, rx, n in BUCKETS:
    has_sip = df.text.str.contains(SIP, case=False, regex=True)
    if rx is None:  # tests the is_relevant label
        mask = ~has_sip
    else:
        mask = has_sip & df.text.str.contains(rx, case=False, regex=True)
    pool = df[mask & ~df.uid.isin(used)]
    pool = pool.sample(frac=1, random_state=42)
    got = 0
    for _, r in pool.iterrows():
        if got >= n:
            break
        if src_n.get(r.source, 0) >= SOURCE_CAP.get(r.source, 0):
            continue
        picked.append({**r.to_dict(), "pick_reason": name})
        used.add(r.uid)
        src_n[r.source] += 1
        got += 1

gs = pd.DataFrame(picked)
print(f"{len(gs)} items | by source: {gs.source.value_counts().to_dict()}")
print(gs.pick_reason.value_counts().to_string())

# ---------------------------------------------------------------- Excel
LABELS = {  # column -> allowed values
    "is_relevant": ["yes", "no"],
    "lifecycle_stage": list(T.LIFECYCLE_STAGES),
    "action": list(T.ACTIONS),
    "trigger": list(T.TRIGGERS),
    "age_band": T.SEGMENT_SIGNALS["age_band"],
    "income_type": T.SEGMENT_SIGNALS["income_type"],
    "source_of_money": T.SEGMENT_SIGNALS["source_of_money"],
    "influencer": T.SEGMENT_SIGNALS["influencer"],
    "expected_safe_behaviour": list(T.SAFE_BEHAVIOURS),
}
FREE = ["user_message_variant", "notes"]
INFO = ["uid", "source", "pick_reason", "context", "text"]
cols = INFO + list(LABELS)[:8] + FREE[:1] + ["expected_safe_behaviour", "notes"]

wb = Workbook()
ws = wb.active
ws.title = "golden_set"
lists = wb.create_sheet("lists")  # dropdown source values
for j, (col, vals) in enumerate(LABELS.items(), 1):
    lists.cell(1, j, col)
    for i, v in enumerate(vals, 2):
        lists.cell(i, j, v)

ws.append(cols)
for _, r in gs.iterrows():
    ws.append([r.get(c, "") for c in INFO] + [""] * (len(cols) - len(INFO)))

head_fill = PatternFill("solid", fgColor="DDEBF7")
label_fill = PatternFill("solid", fgColor="FFF2CC")
for c in ws[1]:
    c.font = Font(bold=True)
    c.fill = head_fill if c.value in INFO else label_fill
widths = {"uid": 10, "source": 11, "pick_reason": 20, "context": 25, "text": 70, "user_message_variant": 40, "notes": 30}
for idx, col in enumerate(cols, 1):
    letter = ws.cell(1, idx).column_letter
    ws.column_dimensions[letter].width = widths.get(col, 18)
    for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    if col in LABELS:
        j = list(LABELS).index(col) + 1
        L = lists.cell(1, j).column_letter
        dv = DataValidation(type="list", formula1=f"=lists!${L}$2:${L}${len(LABELS[col]) + 1}", allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{letter}2:{letter}{len(gs) + 1}")
ws.freeze_panes = "F2"

# how-to sheet with definitions
guide = wb.create_sheet("how_to_label", 0)
lines = [
    "HOW TO LABEL (do this yourself, before looking at any AI output)",
    "1. Read 'text' (and 'context' = video/thread title). Fill every yellow column using the dropdowns.",
    "2. is_relevant = no if it is not about starting/continuing/pausing/stopping a SIP. Then leave the rest blank.",
    "3. Segment columns: only fill if the person SAYS it (e.g. 'I am a student'). Otherwise 'unknown'.",
    "4. trigger = the MAIN reason. Don't pick negative_returns just because they stopped.",
    "5. user_message_variant: rewrite the item as a question a user might type into the MVP chatbot.",
    "6. expected_safe_behaviour: what the MVP should do with that question.",
    "7. Do NOT change uid. Save the file; don't compare with AI labels yet.",
    "",
]
for k, d in [("lifecycle_stage", T.LIFECYCLE_STAGES), ("action", T.ACTIONS),
             ("trigger", T.TRIGGERS), ("expected_safe_behaviour", T.SAFE_BEHAVIOURS)]:
    lines.append(k.upper())
    lines += [f"   {v}: {d[v][0] if isinstance(d[v], tuple) else d[v]}" for v in d]
    lines.append("")
for line in lines:
    guide.append([line])
guide["A1"].font = Font(bold=True, size=13)
guide.column_dimensions["A"].width = 120

out = ROOT / "data" / "golden_set.xlsx"
wb.save(out)
print(f"Saved -> {out.relative_to(ROOT)}")
