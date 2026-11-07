"""SIP Continuation Discovery Engine: public Streamlit app (Step 6).

Run locally:  streamlit run streamlit_app.py
Cloud: put GEMINI_API_KEY, GROQ_API_KEY, GEMINI_MODEL, GEMINI_QUALITY_MODEL, GROQ_MODEL in Streamlit Secrets.
"""
import datetime
import html
import json
import math
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

os.environ.setdefault("LLM_MIN_GAP", "2")  # app traffic is light; batch scripts keep 6.5 s

import taxonomy as T  # noqa: E402
from llm import ask_json  # noqa: E402
import step5_extract as X  # noqa: E402  (same prompt + validation as the batch engine)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CHOSEN = "involuntary_payment_and_refund_issues"
LAPSE = {"stopped", "paused", "reduced", "considering_stop", "lapsed_involuntary", "setup_failed", "redeemed"}
SESSION_CAP, DAILY_CAP = 12, 250  # protect the free API quota
EVIDENCE_LOG_URL = os.getenv("EVIDENCE_LOG_URL", "")
# Okabe-Ito colour-blind-safe palette
# v2 palette: inspired by Groww's clean fintech look (mint accent, slate ink), kept colour-blind-safe:
# highlight = mint vs very light slate (big lightness gap), never green-vs-red as the only signal.
ACCENT, ACCENT_SOFT, INDIGO, INK, MUTED, LINE, SOFT = "#00B386", "#E6F7F2", "#5367FF", "#44475B", "#7C7E8C", "#E9ECEF", "#F5F7FA"
BLUE, ORANGE, GREY, GREEN, VERMILION, SKY = "#CBD3E1", ACCENT, "#CBD3E1", ACCENT, "#EB5B3C", INDIGO

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--accent:#00B386;--accent-soft:#E6F7F2;--indigo:#5367FF;--ink:#44475B;--muted:#7C7E8C;--line:#E9ECEF;--soft:#F5F7FA}
.stApp,.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
.stApp td,.stApp th{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif !important}
.stApp{background:#FFFFFF;color:var(--ink)}
header[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
[data-testid="stMainBlockContainer"],.block-container{max-width:1180px;padding-top:1rem}
.gw-nav{display:flex;align-items:center;justify-content:space-between;padding:4px 0 14px;border-bottom:1px solid var(--line)}
.gw-brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:20px;color:var(--ink);letter-spacing:-.01em}
.gw-mark{width:36px;height:36px;border-radius:10px;background:var(--accent-soft);display:grid;place-items:center;font-size:18px}
.gw-links{display:flex;gap:22px;font-size:15px;color:var(--muted);font-weight:500}
.gw-chip{font-size:13px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-weight:500;background:#fff}
.gw-ticker{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 28px;padding:16px 0 0}
.gw-ticker::-webkit-scrollbar{display:none}
.gw-tick{font-size:13px;color:var(--muted);font-weight:600;letter-spacing:.02em;white-space:nowrap}
.gw-tick b.ok{color:var(--accent);font-weight:600}
.gw-badge{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;border-radius:6px;padding:1px 7px;margin-right:4px}
.gw-badge.ok{background:#E6F7F2;color:#00775A}.gw-badge.warn{background:#FFF1DC;color:#8A5200}
.gw-tick b{color:var(--ink);font-weight:500;margin-left:8px}
.gw-tick i{font-style:normal;color:var(--accent);margin-left:6px}
.gw-hero{text-align:center;padding:4px 0 22px}
.gw-hero h1{font-size:clamp(40px,6.4vw,80px) !important;line-height:1.04 !important;font-weight:800 !important;color:var(--ink) !important;
  letter-spacing:-.035em;margin:10px 0 12px !important;padding:0 !important}
.gw-hero p{max-width:760px;margin:0 auto !important;color:var(--muted);font-size:17px;line-height:1.6}
.gw-pills{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:20px}
.gw-pill{border-radius:999px;padding:10px 18px;font-size:14px;font-weight:600;border:1px solid var(--line);color:var(--ink);background:#fff}
.gw-pill.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.gw-pill .l{color:var(--accent);font-weight:700;font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin-right:8px}
.gw-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:8px 0 6px}
.gw-card{border:1px solid var(--line);border-radius:16px;padding:18px 18px 16px;background:#fff;transition:box-shadow .2s,transform .2s}
.gw-card:hover{box-shadow:0 8px 28px rgba(68,71,91,.08);transform:translateY(-1px)}
.gw-card .k{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.gw-card .k.indigo{color:var(--indigo)}
.gw-card .v{font-size:32px;font-weight:700;color:var(--ink);margin:6px 0 4px;letter-spacing:-.02em}
.gw-card .d{font-size:14px;color:var(--muted);line-height:1.55}
[role="tablist"]{width:100%;gap:0 !important;border-bottom:1px solid var(--line)}
[role="tablist"] [data-testid="stTab"]{flex:1 1 0 !important;justify-content:center !important;padding:14px 4px !important}
[data-testid="stTab"] p{font-size:16px !important;font-weight:500 !important;color:var(--muted)}
[data-testid="stTab"][aria-selected="true"] p{color:var(--ink) !important;font-weight:600 !important}
.stApp h3{font-weight:700 !important;color:var(--ink);letter-spacing:-.015em}
[data-testid="stCaptionContainer"]{opacity:1 !important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted) !important;font-size:13.5px !important}
.stButton>button{border-radius:10px !important;padding:.55rem 1.4rem !important;font-weight:600 !important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important}
[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="textarea"]{border-radius:12px !important}
[data-testid="stExpander"] details{border-radius:12px !important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
.gw-quote{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:12px 16px;margin:8px 0;background:#fff}
.gw-quote .t{font-size:15px;color:var(--ink);line-height:1.55}
.gw-meta{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
.gw-meta span,.gw-meta a{font-size:12px;color:var(--muted);background:var(--soft);border-radius:999px;padding:3px 10px;text-decoration:none}
.gw-meta a:hover{color:var(--accent)}
.gw-section{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin:18px 0 -6px}
.gw-foot{margin-top:30px;padding:18px 0 8px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;text-align:center;line-height:1.7}
@media (max-width:760px){.gw-chip{display:none}[role="tablist"] [data-testid="stTab"]{flex:1 1 0 !important;padding:10px 3px !important;min-width:0}[data-testid="stTab"] p{font-size:13px !important;white-space:normal !important;text-align:center;line-height:1.25}}
</style>
"""

BRIEF_QUESTIONS = [
    "Why do people start a SIP, and what do they expect to happen?",
    "What changes in their behaviour in the months after starting?",
    "What leads investors to pause, reduce or stop a SIP?",
    "What do investors check, and how often, once they have started?",
    "What confuses or worries them inside the app?",
    "What do they do outside the app when they feel unsure?",
    "What separates investors who continue from those who quietly drop off?",
    "How do these patterns differ across user segments (income stability, age, source of money, who influenced them)?",
    "What unmet needs emerge consistently across conversations?",
    "Why do SIP instalments fail even when people want to keep investing?",
]
STAGE_ORDER = ["pre_start", "m0_1", "m2_6", "m7_12", "m12_plus"]
STAGE_LABEL = {"pre_start": "Before 1st SIP", "m0_1": "Month 0–1", "m2_6": "Months 2–6",
               "m7_12": "Months 7–12", "m12_plus": "12+ months"}
SOURCE_LABEL = {"play_store": "Play Store", "app_store": "App Store", "youtube": "YouTube", "tradingqna": "TradingQ&A"}

st.set_page_config(page_title="SIP Discovery Engine", page_icon=":material/insights:", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    items = pd.read_csv(DATA / "engine_items.csv", dtype=str, keep_default_na=False)
    for c in ["is_relevant", "quote_ok", "is_payment_failure"]:
        items[c] = items[c].str.lower().eq("true")
    items["confidence"] = pd.to_numeric(items.confidence, errors="coerce")
    items["source_name"] = items.source.map(SOURCE_LABEL)
    opp = pd.read_csv(DATA / "opportunities.csv")
    counts = pd.read_csv(DATA / "source_counts.csv")
    gold = pd.read_csv(DATA / "golden_agreement.csv")
    themes = json.loads((DATA / "themes.json").read_text(encoding="utf-8"))
    return items, opp, counts, gold, themes


items, opp, counts, gold, themes = load()
rel = items[items.is_relevant]
themed = rel[~rel.theme.isin(["no_signal", "not_relevant"])]


def agreement(field):
    m = gold[f"match_{field}"].dropna().astype(str)
    m = m[m.isin(["True", "False"])]
    return (m == "True").mean() * 100, int((m == "True").sum()), len(m)


# ------------------------------------------------------------------ usage cap
def _usage_file():
    return Path(tempfile.gettempdir()) / "sip_engine_usage.json"


def can_call() -> tuple[bool, str]:
    if st.session_state.get("llm_calls", 0) >= SESSION_CAP:
        return False, f"You've used this session's {SESSION_CAP} AI calls (this keeps the free API quota alive). Reload the page later."
    try:
        u = json.loads(_usage_file().read_text())
    except Exception:
        u = {}
    if u.get(str(datetime.date.today()), 0) >= DAILY_CAP:
        return False, "Today's shared AI quota for this demo is used up. The dashboard and validation tabs still work."
    return True, ""


def count_call(n=1):
    st.session_state.llm_calls = st.session_state.get("llm_calls", 0) + n
    try:
        f = _usage_file()
        u = json.loads(f.read_text()) if f.exists() else {}
        k = str(datetime.date.today())
        f.write_text(json.dumps({k: u.get(k, 0) + n}))
    except Exception:
        pass


# ------------------------------------------------------------------ retrieval for "Ask the data"
STOP = set("""a an the and or of to in on for is are was were be been do does did i you we they it its this that with as at by
from what why how who when which there their them my me our your about into than then so if not no can will would should
could also more most some any all each per after before up out over just get got people investor investors sip sips""".split())


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def toks(s):
    return [stem(w) for w in re.findall(r"[a-z0-9ऀ-ॿ]+", s.lower()) if w not in STOP and len(w) > 1]


@st.cache_resource
def index():
    docs = rel.assign(doc=(rel.text + " " + rel.unmet_need + " " + rel.what_they_check + " " + rel.theme_name + " "
                           + rel.trigger.str.replace("_", " ") + " " + rel.action.str.replace("_", " ") + " "
                           + rel.outside_app_behaviour.str.replace("_", " ")))
    tf = [Counter(toks(d)) for d in docs.doc]
    dfreq = Counter(w for c in tf for w in c)
    n = len(tf)
    idf = {w: math.log(n / (1 + k)) for w, k in dfreq.items()}
    return docs.reset_index(drop=True), tf, idf


def lexical_scores(words):
    docs, tf, idf = index()
    qt = set(toks(" ".join(words)))
    return docs, [sum(min(c[w], 3) * idf.get(w, 0) for w in qt) for c in tf]


def plan_query(q):
    """Step 1: map the question onto the engine's own tags (themes / triggers / actions) + search words."""
    theme_menu = "\n".join(f"- {t['id']}: {t['name']}" for t in themes["themes"])
    prompt = f"""Map this research question onto a tagged dataset of SIP comments.
QUESTION: {q}

THEMES:
{theme_menu}
TRIGGERS: {", ".join(T.TRIGGERS)}
ACTIONS: {", ".join(T.ACTIONS)}
OUTSIDE-APP BEHAVIOURS: youtube, friends_family, reddit_forum, advisor_ca, other

Pick only the tags that directly help answer the question (it is fine to pick none of a type).
Also give 8-15 search keywords, including spelling variants and Hinglish words (e.g. installment/instalment, band karna).
Return JSON: {{"themes": [...max 4 ids], "triggers": [...max 5], "actions": [...max 5], "outside": [...max 3], "keywords": [...]}}"""
    res, _ = ask_json(prompt, system="You map questions to dataset filters. Output JSON only.")
    pick = lambda key, allowed, n: [x for x in res.get(key, []) if x in allowed][:n]  # noqa: E731
    return {"themes": pick("themes", {t["id"] for t in themes["themes"]}, 4),
            "triggers": pick("triggers", set(T.TRIGGERS) - {"none", "other"}, 5),
            "actions": pick("actions", set(T.ACTIONS) - {"unknown"}, 5),
            "outside": pick("outside", {"youtube", "friends_family", "reddit_forum", "advisor_ca", "other"}, 3),
            "keywords": [str(k) for k in res.get("keywords", [])][:15]}


def retrieve(q, plan, k=40, per_source=14):
    docs, scores = lexical_scores(plan["keywords"] + [q])
    docs = docs.assign(_score=scores)
    mask = (docs.theme.isin(plan["themes"]) | docs.trigger.isin(plan["triggers"]) | docs.action.isin(plan["actions"])
            | docs.outside_app_behaviour.isin(plan["outside"]))
    pool = docs[mask] if mask.sum() >= 10 else docs[docs._score > 0]
    pool = pool.assign(_rank=pool._score + 2 * pool.confidence.fillna(0.5)).sort_values("_rank", ascending=False)
    # keep a mix of sources so one forum doesn't dominate the evidence
    picked = pool.groupby("source", group_keys=False).head(per_source).sort_values("_rank", ascending=False).head(k)
    return picked, pool


def dataset_stats(pool):
    """Counts over the WHOLE matching set (not just the 40 shown), so answers can quantify."""
    n_rel = len(rel)
    lines = [f"Matching items in the full dataset: {len(pool)} of {n_rel} relevant comments."]
    for col, label in [("theme_name", "theme"), ("trigger", "trigger"), ("action", "action"), ("source", "source")]:
        vc = pool[col].value_counts().head(6)
        lines.append(f"By {label}: " + ", ".join(f"{k} {v}" for k, v in vc.items()))
    known = pool[pool.lifecycle_stage.isin(STAGE_ORDER)].lifecycle_stage.value_counts()
    lines.append("By lifecycle stage (known only): " + ", ".join(f"{STAGE_LABEL[k]} {v}" for k, v in known.items()))
    return "\n".join(lines)


def quote_match(quote, texts, near=0.92):
    """'exact' | 'near-exact' (≥92% of characters match: typo/spacing fixes) | 'not found'."""
    from difflib import SequenceMatcher
    norm = lambda s: re.sub(r"[^a-z0-9ऀ-ॿ]", "", s.lower())  # noqa: E731
    qn = norm(quote)
    if not qn:
        return "exact"
    best = 0.0
    for t in texts:
        tn = norm(t)
        if qn in tn:
            return "exact"
        sm = SequenceMatcher(None, qn, tn, autojunk=False)
        # count only runs of 4+ chars, so scattered single letters in a long text can't fake a match
        best = max(best, sum(b.size for b in sm.get_matching_blocks() if b.size >= 4) / len(qn))
    return "near-exact" if best >= near else "not found"


def clean_citations(text, valid):
    """Quality gate: keep only citations that point to items we actually gave the model."""
    removed = 0

    def fix(m):
        nonlocal removed
        ids = re.findall(r"[a-z]{2}_\d{5}", m.group(1))
        good = [i for i in ids if i in valid]
        removed += len(ids) - len(good)
        return f"[{', '.join(good)}]" if good else ""
    if not re.search(r"[a-z]{2}_\d{5}", text):
        return text, 0, []
    text = re.sub(r"\[([^\]]*[a-z]{2}_\d{5}[^\]]*)\]", fix, text)
    cited = [i for i in re.findall(r"[a-z]{2}_\d{5}", text) if i in valid]
    return text, removed, list(dict.fromkeys(cited))


@st.cache_resource
def answer_cache(version: int = 3):  # bump to discard answers cached by an older answer format
    return {"_version": version}


def ask_the_data(q):
    plan = plan_query(q)
    hits, pool = retrieve(q, plan)
    if len(hits) < 3:
        return {"answer": "", "hits": hits, "plan": plan, "strength": "none", "removed": 0, "provider": "", "calls": 1}
    ev = [{"id": r.uid, "source": SOURCE_LABEL.get(r.source, r.source), "theme": r.theme_name,
           "stage": r.lifecycle_stage, "action": r.action, "trigger": r.trigger, "text": r.text[:350]}
          for r in hits.itertuples()]
    stats = dataset_stats(pool)
    prompt = f"""Answer the research question for a product team, using ONLY the material below
(public comments about SIPs in India, tagged by an AI pipeline).

DATASET STATS (counts over ALL matching comments; use these for numbers):
{stats}

EVIDENCE ({len(ev)} sample comments; use these for examples and quotes):
{json.dumps(ev, ensure_ascii=False)}

Rules:
- Lead with the 2-4 most important patterns. Use the DATASET STATS for counts and shares ("x of N").
- Cite evidence ids in square brackets after each claim, e.g. [pl_00072] or [pl_00072, yo_01842].
- Include 2-3 short EXACT quotes copied from the evidence, in double quotes.
- Say plainly what the data can NOT tell (e.g. segment info is rarely stated).
- Never give investment advice, fund names or return predictions.
- Max 230 words, markdown bullets.

Return JSON: {{"answer": "markdown", "evidence_strength": "strong|moderate|weak"}}

QUESTION: {q}"""
    res, provider = ask_json(prompt, system="You are a careful user-research analyst. Output JSON only.")
    text, removed, cited = clean_citations(str(res.get("answer", "")), set(hits.uid))
    # quality gate 2: quotes must exist in the evidence (exact, or near-exact = typo/spacing fixes only)
    # pair quote marks strictly left to right (straight or curly), then keep the substantial ones
    quotes = [m.group(1) or m.group(2) for m in re.finditer(r'"([^"]*)"|“([^”]*)”', text)]
    quotes = [qq for qq in quotes if len(qq.strip()) >= 15]
    fake = [qq for qq in quotes if quote_match(qq, hits.text) == "not found"]
    return {"answer": text, "hits": hits, "plan": plan, "pool_n": len(pool), "cited": cited, "removed": removed,
            "quotes": len(quotes), "fake_quotes": fake, "strength": res.get("evidence_strength", "?"),
            "provider": provider, "calls": 2}


# ------------------------------------------------------------------ live tagging ("Analyse new text")
def tag_texts(lines):
    src = [{"uid": f"new_{i:02d}", "source": "pasted", "title_or_context": "", "text": t[:1200]} for i, t in enumerate(lines)]
    prompt = X.INSTRUCTIONS.format(taxonomy=T.prompt_block(), items=json.dumps(src, ensure_ascii=False))
    res, provider = ask_json(prompt, system=X.SYSTEM)
    got = {str(x.get("uid")): x for x in res.get("items", []) if isinstance(x, dict)}
    rows = []
    for s in src:
        rec, fixes = X.clean(got.get(s["uid"], {}), s)
        rec["fixes"] = fixes
        rec["text"] = s["text"]
        rows.append(rec)
    # theme assignment (same theme list as the engine)
    menu = "\n".join(f"- {t['id']}: {t['name']} - {t['definition']}" for t in themes["themes"])
    to_theme = [{"uid": r["uid"], "trigger": r["trigger"], "action": r["action"], "unmet_need": r["unmet_need"],
                 "quote": r["evidence_quote"]} for r in rows if r["is_relevant"]]
    if to_theme:
        res2, _ = ask_json(f"Assign each item to exactly ONE theme id.\nTHEMES:\n{menu}\n\n"
                           f'Return {{"items": [{{"uid": ..., "theme": ...}}]}}\n\nITEMS:\n{json.dumps(to_theme, ensure_ascii=False)}',
                           system="You are a senior user-research analyst. Output JSON only.")
        tmap = {str(x.get("uid")): x.get("theme") for x in res2.get("items", [])}
    else:
        tmap = {}
    names = {t["id"]: t["name"] for t in themes["themes"]}
    for r in rows:
        r["theme"] = names.get(tmap.get(r["uid"]), "Other Unmet Needs") if r["is_relevant"] else "Not relevant"
    return rows, provider, 1 + bool(to_theme)


# ------------------------------------------------------------------ helpers
def bar(df, x, y, color=None, highlight=None, height=None, fmt=None):
    d = df.sort_values(x, ascending=False).copy()
    d["_c"] = "base" if highlight is None else d[y].eq(highlight).map({True: "hl", False: "base"})
    order = d[y].tolist()  # explicit order: layered charts ignore sort="-x"
    ch = alt.Chart(d).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X(f"{x}:Q", title=None, axis=alt.Axis(grid=False)),
        y=alt.Y(f"{y}:N", sort=order, title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False, labelFontSize=12)),
        color=alt.Color("_c:N", scale=alt.Scale(domain=["base", "hl"], range=[color or BLUE, ORANGE]), legend=None),
        tooltip=[alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:Q", format=fmt or "")],
    )
    text = ch.mark_text(align="left", dx=3, fontSize=12).encode(text=alt.Text(f"{x}:Q", format=fmt or ""),
                                                                color=alt.value(MUTED))
    return (ch + text).properties(height=height or max(130, 30 * len(d)))


def quote_cards(df, n=6):
    df = df[df.quote_ok & (df.evidence_quote.str.len() > 15)].sort_values("confidence", ascending=False).head(n)
    if df.empty:
        st.caption("No verified quotes.")
    esc = html.escape  # review text is untrusted: always escape before rendering as HTML
    cards = []
    for r in df.itertuples():
        stage = STAGE_LABEL.get(r.lifecycle_stage, "stage unknown")
        cards.append(
            f'<div class="gw-quote"><div class="t">“{esc(r.evidence_quote)}”</div><div class="gw-meta">'
            f'<span>{esc(SOURCE_LABEL.get(r.source, r.source))}</span><span>{esc(stage)}</span>'
            f'<span>{esc(r.action.replace("_", " "))}</span>'
            f'<a href="{esc(r.url, quote=True)}" target="_blank" rel="noopener noreferrer">source</a>'
            f'<span>{esc(r.uid)}</span></div></div>')
    st.markdown("".join(cards), unsafe_allow_html=True)


def style(ch):
    """Light, minimal chart styling to match the page."""
    return (ch.configure(font="Inter").configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, domainColor=LINE, tickColor=LINE, gridColor="#F0F2F5",
                            labelFontSize=12, titleFontSize=12, titleFontWeight=500)
            .configure_legend(labelColor=INK, labelFontSize=12, symbolType="circle"))


def show(ch):
    st.altair_chart(style(ch), width="stretch", theme=None)


def card(kicker, value, desc, indigo=False):
    return (f'<div class="gw-card"><div class="k{" indigo" if indigo else ""}">{kicker}</div>'
            f'<div class="v">{value}</div><div class="d">{desc}</div></div>')


# ------------------------------------------------------------------ header (Groww-inspired: nav, ticker, hero)
raw_total = int(counts[counts.source != "TOTAL"].raw.sum())
ticks = [("RAW ITEMS", f"{raw_total:,}", ""), ("SIP-RELEVANT", f"{len(items):,}", ""),
         ("AI-RELEVANT", f"{len(rel):,}", ""), ("WITH A NEED / TRIGGER", f"{len(themed):,}", ""),
         ("THEMES", str(len(themes["themes"])), ""),
         ("AI vs HUMAN (TRIGGER)", f"{agreement('trigger')[0]:.0f}%", "ok"),
         ("QUOTES VERIFIED", f"{rel.quote_ok.mean() * 100:.0f}%", "ok")]
st.markdown(
    '<div class="gw-nav"><div class="gw-brand"><div class="gw-mark"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00B386" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19V10"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M21 19H3"/></svg></div>SIP Discovery Engine</div>'
    '<div class="gw-chip">Student research · not investment advice</div></div>'
    '<div class="gw-ticker">' + "".join(f'<span class="gw-tick">{k}<b class="{a}">{v}</b></span>'
                                       for k, v, a in ticks) + '</div>'
    '<div class="gw-hero"><h1>Why first SIPs stop</h1>'
    f'<p>An AI discovery engine over <b>{raw_total:,}</b> public conversations about SIPs in India. It finds, quantifies and '
    'ranks what stops first-time investors from still having an active SIP 12 months after their first one.</p>'
    '<div class="gw-pills">'
    '<span class="gw-pill"><span class="l">Case</span>Groww · first-time MF investors</span>'
    '<span class="gw-pill"><span class="l">Metric</span>Active SIP at 12 months</span>'
    '<span class="gw-pill"><span class="l">Focus</span>SIP payment failures</span>'
    '</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Findings", "Ask the data", "Analyse new text", "How it works"])

# ================================================================== TAB 1: findings
with tab1:
    lapse = rel[rel.action.isin(LAPSE)]
    mkt = (themed.theme == "negative_returns_and_market_disappointment").mean() * 100
    pf = rel[rel.is_payment_failure]
    st.markdown('<div class="gw-cards">'
                + card("Minor driver", f"{mkt:.0f}%", "of themed mentions blame falling or flat returns. App/trust issues, "
                       "payment failures and setup friction dominate.")
                + card("Chosen opportunity", f"{len(pf)} items", "SIP payment failures: users still want to invest, but "
                       "instalments fail. Peaks in months 2–6. Most Groww-specific evidence.")
                + card("Close race", "5.7 – 8.8", "Scores of the top 4 opportunities. Source mix and the link to the "
                       "metric decided the pick, not the score alone.", indigo=True)
                + "</div>", unsafe_allow_html=True)

    st.subheader("Ranked opportunities")
    st.caption("Score = Reach (mentions ÷ biggest theme) × Metric impact (A/B = 3, C = 2, +1 if ≥50% are stop/lapse "
               "actions; D/E = 1) × Confidence (share of sources where the theme is ≥3% of items) × Addressability "
               "(1–3: fixable without advice or fear). Themes reviewed and corrected by a human. \"Chosen\" = picked at the decision gate.")
    t = opp.copy()
    t.insert(0, "Pick", t.theme.eq(CHOSEN).map({True: "Chosen", False: ""}))
    st.dataframe(
        t[["Pick", "rank", "name", "node", "mentions", "share_%", "lapse_action_%", "metric_impact", "confidence",
           "addressability", "score"]],
        hide_index=True, width="stretch",
        column_config={
            "Pick": st.column_config.TextColumn("Pick", width="small"),
            "rank": "#", "name": st.column_config.TextColumn("Theme", width="large"), "node": "Node",
            "mentions": "Mentions", "share_%": st.column_config.NumberColumn("Share", format="%.1f%%"),
            "lapse_action_%": st.column_config.NumberColumn("Stop/lapse actions", format="%.0f%%"),
            "metric_impact": "Impact", "confidence": "Confidence", "addressability": "Addressability",
            "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=float(t.score.max()), format="%.2f"),
        })
    st.caption("Node: A = SIP goes live · B = instalments keep succeeding (involuntary lapse) · C = user chooses to "
               "continue (voluntary lapse) · D = re-entry/switch · E = engagement · X = other")

    a, b = st.columns(2)
    with a:
        st.markdown("**What's behind stop / pause / lapse actions** (main trigger)")
        lt = lapse.trigger.value_counts().rename_axis("trigger").reset_index(name="items")
        lt["trigger"] = lt.trigger.str.replace("_", " ")
        lt["pct"] = lt["items"] / lt["items"].sum() * 100
        show(bar(lt.head(9), "pct", "trigger", highlight="payment failure", fmt=".0f"))
        st.caption(f"{len(lapse)} relevant items whose action is stop / pause / reduce / lapse / redeem. % of those items.")
    with b:
        st.markdown("**When it happens:** all relevant items vs payment failures (known stage only)")
        s_all = rel[rel.lifecycle_stage.isin(STAGE_ORDER)].lifecycle_stage.value_counts(normalize=True) * 100
        s_pf = pf[pf.lifecycle_stage.isin(STAGE_ORDER)].lifecycle_stage.value_counts(normalize=True) * 100
        sd = pd.DataFrame({"All relevant": s_all, "Payment failures": s_pf}).reindex(STAGE_ORDER).fillna(0)
        sd = sd.rename(index=STAGE_LABEL).reset_index(names="stage").melt("stage", var_name="group", value_name="pct")
        ch = alt.Chart(sd).mark_bar().encode(
            x=alt.X("stage:N", sort=[STAGE_LABEL[s] for s in STAGE_ORDER], title=None, axis=alt.Axis(labelAngle=0)),
            xOffset="group:N", y=alt.Y("pct:Q", title="% of items with a known stage"),
            color=alt.Color("group:N", scale=alt.Scale(range=[GREY, ORANGE]), legend=alt.Legend(orient="top", title=None)),
            tooltip=["stage", "group", alt.Tooltip("pct:Q", format=".0f")]).properties(height=260)
        show(ch)
        st.caption("Payment failures peak in months 2–6, inside the 12-month window. Most other talk is before the first SIP.")

    st.divider()
    st.markdown('<div class="gw-section">Chosen opportunity</div>', unsafe_allow_html=True)
    st.subheader("Deep dive: why SIP payments fail")
    d1, d2 = st.columns([1.1, 1])
    with d1:
        subs = Counter(s.strip() for v in pf.pf_subcauses for s in v.split(";") if s.strip())
        sc = pd.DataFrame(subs.items(), columns=["sub-cause", "items"])
        sc["pct"] = sc["items"] / len(pf) * 100
        show(bar(sc, "pct", "sub-cause", color=ORANGE, fmt=".0f"))
        st.caption(f"% of {len(pf)} payment-failure items (keyword rules; one item can match several).")
    with d2:
        st.markdown(
            "- Public complaints are mostly **system-side**: autopay/mandate failing, money debited but no units, double debits.\n"
            "- Only a handful mention **low balance or salary timing**. Our hypothesis: those failures are *self-blamed* and never "
            "reviewed, so they're **invisible, not absent**. The interviews test this.\n"
            "- More than a quarter add that **support didn't resolve it**. One failure becomes a trust problem, and people switch apps.")
    quote_cards(pf, 5)

    st.divider()
    st.subheader("Theme explorer")
    names = opp.sort_values("rank")[["theme", "name"]].values.tolist()
    sel = st.selectbox("Theme", [n for _, n in names], index=[i for i, (tid, _) in enumerate(names) if tid == CHOSEN][0])
    tid = dict((n, t_) for t_, n in names)[sel]
    srcs = st.multiselect("Sources", list(SOURCE_LABEL.values()), default=list(SOURCE_LABEL.values()))
    g = themed[(themed.theme == tid) & themed.source_name.isin(srcs)]
    th = next(t_ for t_ in themes["themes"] if t_["id"] == tid)
    st.markdown(f"**{th['name']}**: {th['definition']}  \nNode **{th['node']}** · addressability **{th['addressability']}** "
                f"({th.get('addressability_reason', '')})")
    if th.get("review_changes"):
        st.caption("Human review changes: " + " | ".join(th["review_changes"]))
    e1, e2, e3 = st.columns(3)
    e1.metric("Mentions", len(g))
    e2.metric("Stop / lapse actions", f"{g.action.isin(LAPSE).mean() * 100:.0f}%" if len(g) else "–")
    e3.metric("From Groww app reviews", f"{g.source.isin(['play_store', 'app_store']).mean() * 100:.0f}%" if len(g) else "–")
    f1, f2 = st.columns(2)
    with f1:
        if len(g):
            ac = g.action.str.replace("_", " ").value_counts().rename_axis("action").reset_index(name="items")
            show(bar(ac.head(8), "items", "action"))
    with f2:
        if len(g):
            so = g.source_name.value_counts().rename_axis("source").reset_index(name="items")
            show(bar(so, "items", "source", color=SKY))
    quote_cards(g, 6)
    with st.expander("Unmet needs in this theme (AI-extracted, sample)"):
        for u in g[g.unmet_need.str.len() > 0].unmet_need.drop_duplicates().head(15):
            st.markdown(f"- {u}")

    st.divider()
    st.subheader("Segments: what public data can (not) tell us")
    seg_rows = [(col, int((rel[col] != "unknown").sum())) for col in ["income_type", "age_band", "source_of_money"]]
    st.markdown(" · ".join(f"**{c.replace('_', ' ')}** stated in {n} of {len(rel):,} items" for c, n in seg_rows))
    st.caption("Under 4% of items state income, age or source of money, and on the golden set the AI *invented* segment info in 6 of "
               "24 items. So segment comparisons are **not** drawn from this data; the segment is chosen and validated "
               "through 5–6 user interviews.")

# ================================================================== TAB 2: ask
with tab2:
    st.markdown("Ask a research question. The engine **retrieves** the most relevant of the "
                f"{len(rel):,} comments and an LLM answers **only from them**, citing each claim. "
                "Two automatic checks run on every answer: citations must point to retrieved items, and quotes must "
                "exist word for word in the comments.")
    preset = st.selectbox("Pick a question from the brief, or write your own below", ["(write my own)"] + BRIEF_QUESTIONS, index=10)
    q = st.text_input("Question", value="" if preset == "(write my own)" else preset, max_chars=300)
    out = None
    if st.button("Ask the data", type="primary", disabled=not q.strip()):
        cache = answer_cache()
        key = q.strip().lower()
        if key in cache:
            out = cache[key]
        else:
            ok, why = can_call()
            if not ok:
                st.warning(why)
            else:
                with st.spinner("Retrieving evidence and drafting an answer…"):
                    try:
                        out = ask_the_data(q.strip())
                        count_call(out.get("calls", 2))
                        if out["answer"]:
                            cache[key] = out
                    except Exception as e:
                        st.error(f"The AI service is busy right now ({str(e)[:120]}). Please try again in a minute.")
    if out is not None:
        if not out["answer"]:
            st.warning("Not enough matching comments to answer this reliably. Try other words (e.g. 'pause', "
                       "'autopay', 'returns', 'YouTube').")
        else:
            badge = ('<span class="gw-badge ok">Passed</span> all citations verified' if not out["removed"]
                     else f'<span class="gw-badge warn">Check</span> {out["removed"]} unverifiable citation(s) removed')
            qb = (f'<span class="gw-badge ok">Passed</span> {out["quotes"]} quote(s) verified against the comments' if not out["fake_quotes"]
                  else f'<span class="gw-badge warn">Check</span> {len(out["fake_quotes"])} of {out["quotes"]} quote(s) not found in the comments; treat them as paraphrase')
            st.markdown(f"<small>**Quality check:** {badge} · {qb} · evidence: {out['strength']} · "
                        f"{out.get('pool_n', 0)} matching comments, {len(out['hits'])} sampled as evidence · "
                        f"{out['provider']}</small>", unsafe_allow_html=True)
            p = out["plan"]
            st.caption("Searched by the engine's tags → " + " · ".join(
                f"{k}: {', '.join(v)}" for k, v in p.items() if v and k != "keywords") + (
                f" · keywords: {', '.join(p['keywords'][:8])}" if p.get("keywords") else ""))
            st.markdown(out["answer"])
            cited = out["hits"][out["hits"].uid.isin(out["cited"])]
            with st.expander(f"Cited comments ({len(cited)})", expanded=False):
                for r in cited.itertuples():
                    st.markdown(f"**`{r.uid}`** · {SOURCE_LABEL.get(r.source, r.source)} · {r.theme_name} · "
                                f"[source]({r.url})  \n{r.text[:500]}")
            with st.expander(f"All retrieved comments ({len(out['hits'])})"):
                st.dataframe(out["hits"][["uid", "source", "theme_name", "lifecycle_stage", "action", "trigger", "text"]],
                             hide_index=True, width="stretch")
    st.caption(f"AI calls this session: {st.session_state.get('llm_calls', 0)}/{SESSION_CAP}. Answers are cached, so "
               "repeating a question is free. Research tool only; not investment advice.")

# ================================================================== TAB 3: analyse new text
with tab3:
    st.markdown("Paste **new** comments (one per line, up to 8). They go through the **same prompt, taxonomy and "
                "validation** the engine used on all 2,237 items, live.")
    example = ("Meri SIP is mahine fail ho gayi, account me paise the phir bhi autopay nahi hua\n"
               "Started my first SIP 4 months ago, returns are still negative, thinking of stopping\n"
               "Great app, very easy to use")
    txt = st.text_area("Comments", value=example, height=140)
    lines = [l.strip() for l in txt.splitlines() if l.strip()][:8]
    rows = None
    if st.button("Tag these comments", type="primary", disabled=not lines):
        ok, why = can_call()
        if not ok:
            st.warning(why)
        else:
            with st.spinner("Tagging…"):
                try:
                    rows, provider, ncalls = tag_texts(lines)
                    count_call(ncalls)
                except Exception as e:
                    st.error(f"The AI service is busy right now ({str(e)[:120]}). Please try again in a minute.")
    if rows is not None:
        df = pd.DataFrame(rows)
        df["quote check"] = df.quote_ok.map({True: "found in text", False: "not found in text"})
        df["fixed values"] = df.fixes.map(lambda f: ", ".join(f) if f else "none")
        df["segment (only if stated)"] = df.apply(
            lambda r: ", ".join(f"{k}={r[k]}" for k in T.SEGMENT_SIGNALS if r[k] != "unknown") or "unknown", axis=1)
        for r in df.to_dict("records"):
            with st.container(border=True):
                st.markdown(f"**“{r['text'][:300]}”**")
                if not r["is_relevant"]:
                    st.markdown("**Not relevant** to SIP continuation (e.g. general praise, stocks/IPO only)")
                    continue
                g1, g2, g3, g4 = st.columns(4)
                g1.markdown(f"<small>Stage</small><br>**{STAGE_LABEL.get(r['lifecycle_stage'], 'unknown')}**", unsafe_allow_html=True)
                g2.markdown(f"<small>Action</small><br>**{r['action'].replace('_', ' ')}**", unsafe_allow_html=True)
                g3.markdown(f"<small>Trigger → node</small><br>**{r['trigger'].replace('_', ' ')} → {r['node']}**", unsafe_allow_html=True)
                g4.markdown(f"<small>Theme</small><br>**{r['theme']}**", unsafe_allow_html=True)
                st.markdown(f"Unmet need: *{r['unmet_need'] or '–'}*  \n"
                            f"Evidence: “{r['evidence_quote']}” ({'found in text' if r['quote_ok'] else 'not found in text'}) · "
                            f"segment: {r['segment (only if stated)']} · confidence {r['confidence']:.2f} · "
                            f"fixed values: {r['fixed values']}")
        with st.expander("Raw table"):
            st.dataframe(df[["text", "is_relevant", "lifecycle_stage", "action", "trigger", "node", "theme", "unmet_need",
                             "evidence_quote", "quote check", "segment (only if stated)", "confidence", "fixed values"]],
                         hide_index=True, width="stretch")
        st.caption(f"Tagged by {provider}. **Checks applied:** every value forced into the taxonomy (see 'fixed values'), "
                   "evidence quote verified against your text, decomposition node derived from the trigger. "
                   "Known weakness (from the golden set): the model sometimes assumes an action, or invents segment info.")
        with st.expander("What the tags mean"):
            st.markdown("**Node:** " + " · ".join(f"{k} = {v}" for k, v in T.NODES.items()))
            st.markdown("**Triggers:** " + " · ".join(f"`{k}` {v[0]}" for k, v in T.TRIGGERS.items()))

# ================================================================== TAB 4: how it works
with tab4:
    st.subheader("Pipeline")
    st.graphviz_chart("""
digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#E6F7F2", color="#00B386", fontcolor="#44475B", fontname="Helvetica", fontsize=11];
 a [label="1. Collect\\nPlay Store · App Store\\nYouTube · TradingQ&A\\n13,609 items"];
 b [label="2. Clean\\ndedupe · strip PII\\nlength + SIP filter\\n2,237 items"];
 c [label="3. Tag (Gemini)\\nfixed taxonomy, JSON\\nbatches of 20\\nvalidated + quote check"];
 d [label="4. Themes\\nAI proposes 12\\nhuman review → 13"];
 e [label="5. Quantify + score\\nReach × Impact ×\\nConfidence × Addressability"];
 f [label="6. Validate\\n24-item golden set"];
 g [label="Ranked opportunities\\n→ decision gate", fillcolor="#EEF0FF", color="#5367FF"];
 edge [color="#9AA3B5"]; a->b->c->d->e->g; c->f; f->g [style=dashed]; }""")
    st.subheader("Sources and volume")
    sc = counts.copy()
    sc["source"] = sc.source.map(SOURCE_LABEL).fillna(sc.source)
    sc.loc[len(sc)] = ["Reddit (blocked: HTTP 403 without API keys)", 0, 0, 0, 0]
    sc = pd.concat([sc[sc.source != "TOTAL"], sc[sc.source == "TOTAL"]])
    st.dataframe(sc.rename(columns={"raw": "Raw", "after_dedupe": "After dedupe", "after_length": "After length filter",
                                    "sip_relevant": "SIP-relevant"}), hide_index=True, width="stretch")
    st.caption("Cleaning: exact dedupe → PII removal (URLs, emails/UPI, phone, PAN, long numbers, usernames, forum quote "
               "blocks; author names never stored) → ≥30 chars and ≥6 words → SIP keywords in English/Hindi/Hinglish.")

    st.subheader("Validation: AI vs golden set (24 items)")
    v = pd.DataFrame([(f.replace("_", " "), *agreement(f)) for f in ["is_relevant", "lifecycle_stage", "trigger", "action"]],
                     columns=["field", "agreement %", "matches", "compared"])
    v["agreement %"] = v["agreement %"].round(0)
    st.dataframe(v, hide_index=True)
    st.caption(f"Segment info invented by the AI: {int(gold.ai_invented_segment.sum())} of {len(gold)} items. "
               "Golden-set labels were drafted by an AI assistant from the text only (without seeing the engine's labels) "
               "and reviewed by the researcher. Small sample: each % is roughly ±15–20 points.")
    st.markdown("""**Where the engine fails, and what we do about it**
- **Assumes an action** when none is stated (`started`/`continued` for people only asking questions). → Action-based numbers are treated as directional only.
- **Confuses "debited but no units"** as a setup failure (A) instead of an involuntary lapse (B). → Payment-failure analysis uses theme **or** trigger.
- **Over-includes generic praise** as relevant. → Items with no need or trigger are excluded from theme shares.
- **Invents segment info** (e.g. "YouTube-influenced" just because a comment is on YouTube). → No segment findings from AI tags.
- **Over-attributes to markets** ("waiting for a correction" → negative returns). → Called out; markets still come out as a minor driver.""")

    st.subheader("Where AI output was rejected or corrected")
    st.markdown("""1. **Off-vocabulary values:** 47 values used a valid tag in the wrong field (e.g. `fund_switch` as an action). Mapped to the intended value instead of "unknown", so switchers count as retained.
2. **Invented quotes:** 3.9% of evidence quotes weren't exact text. They're flagged and never shown as quotes.
3. **Merged theme split:** "Portfolio tracking & return display" mixed comprehension (users don't understand XIRR) with app data errors → split into two themes, items re-assigned.
4. **Wrong decomposition node:** 3 themes moved from E (engagement) to C (voluntary lapse): confusion and trust drive stopping.
5. **Addressability:** negative returns 1 → 2 (explaining a dip is education, not advice); redemption delays 3 → 1 (faster payouts don't keep SIPs alive).""")
    st.caption("The AI's original theme list is kept unchanged (`data/themes_ai_v1.json`); every human change is recorded in `data/themes.json`.")

    st.subheader("Limitations")
    st.markdown("""- **Reddit** is missing (blocked); **X/Instagram** not collected.
- **TradingQ&A** is a Zerodha community, so it skews toward experienced, non-Groww users. Each theme shows its Groww-review share.
- **App Store** feed caps at ~500 recent reviews.
- Public reviews over-represent **angry, system-side failures**; quiet, self-blamed problems are under-represented.
- Tags come from one model (`gemini-3.5-flash-lite`), prompt `extract_v1`; the golden set is small.""")
    if EVIDENCE_LOG_URL:
        st.markdown(f"[Full AI Evidence Log]({EVIDENCE_LOG_URL})")

st.markdown('<div class="gw-foot">Independent student research project · <b>not affiliated with or endorsed by Groww</b> · '
            'public posts only, personal data removed · <b>not investment advice</b><br>'
            'Stack: Python · Gemini API (Groq backup) · Streamlit</div>', unsafe_allow_html=True)
