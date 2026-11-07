"""Builds data/engine_items.csv: one table the Streamlit app loads (text + AI tags + theme + sub-causes).

Run after any change to tagging/themes:  python engine_data.py
"""
import json
import re
from pathlib import Path

import pandas as pd

from step5_extract import load_all_tagged

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# Sub-causes of the chosen opportunity (payment failures). Keyword rules: an item can match several.
PF_SUBCAUSES = {
    "Mandate / autopay failing": r"mandate|auto ?pay|nach|e-?nach|upi auto|autodebit|auto debit|auto-debit",
    "Debited but no units / no refund": r"not allot|n.t allot|no units|units (were|are)? ?not|didn'?t (get|receive) (any )?(units|nav)|not received.{0,20}(units|nav)|refund",
    "Bounce / low balance / penalty": r"bounce|insufficient|penalt|no (fund|balance|money)|low balance|cheque|charges? (by|from) (the )?bank",
    "Double / extra debit": r"twice|double|multiple time|two times|deducted again",
    "Found out later": r"notif|did ?n.t (know|inform)|no (message|sms|alert|mail)|without (any )?(inform|notice)|came to know|not informed|realis|realiz",
    "Support didn't resolve": r"customer (care|support)|support team|ticket|no (one|response)|not respond",
}


def build():
    tagged = pd.DataFrame(load_all_tagged()).drop_duplicates("uid", keep="last")
    base = pd.read_csv(DATA / "filtered_data.csv", dtype=str, keep_default_na=False)
    df = base.merge(tagged, on="uid", how="left")
    assign = pd.read_csv(DATA / "theme_assignments.csv")
    df = df.merge(assign, on="uid", how="left")
    themes = {t["id"]: t["name"] for t in json.loads((DATA / "themes.json").read_text(encoding="utf-8"))["themes"]}
    themes["no_signal"] = "No clear need or trigger"
    df["theme"] = df.theme.fillna("not_relevant")
    df["theme_name"] = df.theme.map(themes).fillna("Not relevant")
    df["is_relevant"] = df.is_relevant.fillna(False).astype(bool)
    pf = df.is_relevant & ((df.theme == "involuntary_payment_and_refund_issues") | (df.trigger == "payment_failure"))
    df["is_payment_failure"] = pf
    df["pf_subcauses"] = ""
    for name, rx in PF_SUBCAUSES.items():
        hit = pf & df.text.str.contains(rx, case=False, regex=True)
        df.loc[hit, "pf_subcauses"] += name + "; "
    keep = ["uid", "source", "date", "url", "rating", "context", "text", "is_relevant", "lifecycle_stage", "action",
            "trigger", "what_they_check", "outside_app_behaviour", "emotion", "unmet_need", "evidence_quote", "quote_ok",
            "confidence", "age_band", "income_type", "source_of_money", "influencer", "node", "theme", "theme_name",
            "is_payment_failure", "pf_subcauses"]
    out = df[keep]
    out.to_csv(DATA / "engine_items.csv", index=False, encoding="utf-8")
    return out


if __name__ == "__main__":
    d = build()
    print(f"{len(d)} rows -> data/engine_items.csv | relevant {int(d.is_relevant.sum())} | payment failures {int(d.is_payment_failure.sum())}")
