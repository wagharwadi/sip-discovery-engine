"""Step 5c: quantify themes and score opportunities.

Score = Reach x Metric impact x Confidence x Addressability
  Reach          = theme's share of relevant mentions, scaled so the biggest theme = 1.0
  Metric impact  = 1-3. A/B (SIP never goes live / involuntary lapse) = 3, C = 2 (+1 if most items in the
                   theme are actual stop/pause/reduce/lapse actions), D/E = 1, X = 0.5
  Confidence     = share of sources where the theme is >= 3% of that source's relevant items
                   (agreement across sources, 0.25-1.0)
  Addressability = 1-3, from data/themes.json (AI proposal, which YOU review)

Outputs: data/opportunities.csv, data/theme_breakdowns.xlsx, step5_results.md
Run: python step5_analyze.py
"""
import json
from pathlib import Path

import pandas as pd

from step5_extract import load_all_tagged

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LAPSE = {"stopped", "paused", "reduced", "considering_stop", "lapsed_involuntary", "setup_failed", "redeemed"}
NODE_IMPACT = {"A": 3, "B": 3, "C": 2, "D": 1, "E": 1, "X": 0.5}


def load():
    tagged = pd.DataFrame(load_all_tagged())
    tagged = tagged.drop_duplicates("uid", keep="last")
    base = pd.read_csv(DATA / "filtered_data.csv", dtype=str, keep_default_na=False)[["uid", "source", "date", "url", "text"]]
    df = base.merge(tagged, on="uid")
    themes = json.loads((DATA / "themes.json").read_text(encoding="utf-8"))["themes"]
    assign = pd.read_csv(DATA / "theme_assignments.csv")
    rel = df[df.is_relevant].merge(assign, on="uid", how="left").fillna({"theme": "unassigned"})
    return df, rel, {t["id"]: t for t in themes}


def pct_table(rel, col):
    t = pd.crosstab(rel.theme, rel[col], normalize="columns").mul(100).round(1)
    t.loc["(n items)"] = rel[col].value_counts()
    return t


def main():
    df, rel_all, themes = load()
    n_nosig = int((rel_all.theme == "no_signal").sum())
    rel = rel_all[rel_all.theme != "no_signal"]  # theme stats use items that carry a need or trigger
    n_sources = rel.source.nunique()
    src_share = pd.crosstab(rel.theme, rel.source, normalize="columns")

    rows = []
    for tid, g in rel.groupby("theme"):
        th = themes.get(tid, {"name": tid, "node": "X", "addressability": 1})
        lapse_share = g.action.isin(LAPSE).mean()
        impact = NODE_IMPACT.get(th["node"], 0.5)
        if th["node"] == "C" and lapse_share >= 0.5:
            impact += 1
        conf = max(0.25, (src_share.loc[tid] >= 0.03).sum() / n_sources)
        top_q = g.sort_values("confidence", ascending=False)
        top_q = top_q[top_q.quote_ok & (top_q.evidence_quote.str.len() > 15)].evidence_quote.head(2).tolist()
        rows.append({
            "theme": tid, "name": th["name"], "node": th["node"], "mentions": len(g),
            "share_%": round(100 * len(g) / len(rel), 1), "lapse_action_%": round(100 * lapse_share, 1),
            "metric_impact": impact, "confidence": round(conf, 2),
            "addressability": float(th.get("addressability", 1)),
            "top_sources": ", ".join(g.source.value_counts().head(2).index),
            "main_stage": g[g.lifecycle_stage != "unknown"].lifecycle_stage.mode().iloc[0]
            if (g.lifecycle_stage != "unknown").any() else "unknown",
            "example_quotes": " | ".join(top_q),
        })
    opp = pd.DataFrame(rows)
    opp["reach"] = (opp.mentions / opp.mentions.max()).round(2)
    opp["score"] = (opp.reach * opp.metric_impact * opp.confidence * opp.addressability).round(2)
    opp = opp[opp.theme.ne("unassigned")].sort_values("score", ascending=False).reset_index(drop=True)
    opp.index += 1
    opp.to_csv(DATA / "opportunities.csv", index_label="rank")

    with pd.ExcelWriter(DATA / "theme_breakdowns.xlsx") as xw:
        opp.to_excel(xw, sheet_name="opportunities", index_label="rank")
        for col in ["source", "lifecycle_stage", "action", "income_type", "age_band", "outside_app_behaviour", "emotion"]:
            sub = rel if col in ("source", "lifecycle_stage", "action", "outside_app_behaviour", "emotion") \
                else rel[rel[col] != "unknown"]
            if len(sub):
                pct_table(sub, col).to_excel(xw, sheet_name=f"by_{col}"[:31])

    # ---- markdown summary
    total, n_rel = len(df), len(rel_all)
    md = [f"# Step 5 results: Discovery Engine\n",
          f"**Tagged:** {total} items · **relevant:** {n_rel} ({100 * n_rel / total:.0f}%) · "
          f"**with a need or trigger (used for themes):** {len(rel)} · no signal: {n_nosig} · "
          f"**providers:** {df.provider.value_counts().to_dict()}\n",
          f"**Quote check:** {100 * df[df.is_relevant].quote_ok.mean():.1f}% of evidence quotes are exact spans of the text "
          f"(the rest were paraphrased/invented by the model).\n",
          "## Ranked opportunities\n",
          "| # | Theme | Node | Mentions | Share | Lapse-action % | Impact | Conf. | Addr. | **Score** |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in opp.iterrows():
        md.append(f"| {i} | {r['name']} | {r.node} | {r.mentions} | {r['share_%']}% | {r['lapse_action_%']}% | "
                  f"{r.metric_impact} | {r.confidence} | {r.addressability:g} | **{r.score}** |")
    md += ["\n## Triggers among items with a stop / pause / reduce / lapse action\n"]
    lapse = rel_all[rel_all.action.isin(LAPSE)]
    for trig, n in lapse.trigger.value_counts().head(8).items():
        md.append(f"- {trig}: {n} ({100 * n / max(1, len(lapse)):.0f}%)")
    md += ["\n## Lifecycle stage (relevant items with a known stage)\n"]
    known = rel_all[rel_all.lifecycle_stage != "unknown"]
    for st, n in known.lifecycle_stage.value_counts().items():
        md.append(f"- {st}: {n} ({100 * n / max(1, len(known)):.0f}%)")
    md += ["\n## Segment signals (only where explicitly stated)\n"]
    for col in ["income_type", "age_band", "source_of_money", "influencer"]:
        vc = rel_all[rel_all[col] != "unknown"][col].value_counts()
        md.append(f"- {col}: {vc.to_dict()} (known for {vc.sum()} of {n_rel})")
    md += ["\n## Top quotes per top-3 opportunity\n"]
    for i, r in opp.head(3).iterrows():
        md.append(f"**{i}. {r['name']}**: {r.example_quotes or '-'}\n")
    md.append("\n*Full breakdowns by source / stage / action / segment: `data/theme_breakdowns.xlsx`.*")
    (ROOT / "step5_results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
