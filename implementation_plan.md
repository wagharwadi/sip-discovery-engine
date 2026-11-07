# Implementation Plan: NextLeap Graduation Project (SIP Continuation)

**Product:** Groww
**Role:** PM, Growth Team
**Goal metric:** % of first-time MF investors who still have an active SIP (≥1 successful instalment in the last 30 days) 12 months after starting their first SIP
**Hard constraints:** no fund/stock recommendations · no fear / FOMO / urgency nudges · nothing presented as investment advice · no PAN / account numbers / portfolio screenshots from respondents
**Deadline:** Mon 9 Nov 2026, 3:59 PM IST. **Internal target: submit by 1:00 PM.**
**Time available from now (Fri 6 Nov, ~11 PM):** about 65 hours, including sleep

---

## 0. The problem statement, in my own words

Starting a SIP on Groww is easy. Keeping it running for 12 months is where users drop off. We are **not told why**. The work is to:

1. **Find the why** using an AI discovery engine over public conversations (Parts 1–2).
2. **Check the why** with 5–6 real people from one segment (Part 3).
3. **State one sharp problem**: segment × moment × root cause, never just "markets fell" (Part 4).
4. **Build, deploy and eval one AI feature** that addresses it, with a visible quality gate or fallback (Part 5).
5. **Test it with 3 users**, then define metrics and risks (Parts 6–8).

What the graders will look for:
- **Traceability.** Every claim in the deck traces back: Metric → Product outcomes → AI findings → Interviews → Problem → MVP.
- **Rigour on the AI work.** A golden set, agreement rates, failures, and places where I overruled the AI.
- **Constraint respect.** No advice, no fear framing, and no dark patterns. Hiding the "Stop SIP" button would count as one.
- **A working public link** that a mentor can use without me present.

### Points in the brief that are easy to miss
| Point | Why it matters |
|---|---|
| The metric counts **any** active SIP, not the *first* SIP | A user who stops SIP #1 but starts SIP #2 is still retained. So "switching" is not churn, and the decomposition must show this. |
| "Active" means a **successful instalment** in the last 30 days | Failed autopay or mandate problems cause *involuntary* lapse even when the user still intends to invest. This is a separate branch from voluntary stopping. |
| The MVP must be measured **against the golden set from the Evidence Log** | Design the MVP's AI core to use the **same taxonomy** as the discovery engine. Then one golden set (~20 items, hand-labelled) can evaluate both. This saves hours. |
| "Deploy to production so another person can use it" | Needs a public URL, no login wall, the API key on the server side, and a usage cap. |
| Show how thinking **evolved**, and where research **challenged** the AI | Keep a running log from hour one, not at the end. |
| No Fellow name anywhere in the deck · 10 slides max · min font 14 (PPT/Slides) · colour-blind-safe · file name `NL_Groww` · <40 MB | Formatting failures cost marks cheaply. |

---

## 1. Why Groww (vs Zerodha Coin and INDmoney)

**Decision: Groww.**

| Criterion | Groww | Zerodha Coin | INDmoney |
|---|---|---|---|
| Fit with "first-time MF investor" | **Strongest.** About 43.6% of all new SIP registrations in India in Jul–Sep 2026 (company figure). It is the default entry point for young first-timers. | Users are mostly existing Kite traders and experienced DIY investors. Few true first-timers. | Skews to affluent, multi-asset users (US stocks, net-worth tracking). |
| Volume of public data for the discovery engine | **Very high.** Huge Play Store review base, constant Reddit/YouTube mentions. | Coin-specific reviews are thin (Coin now sits inside the Kite / Coin web flow). | Moderate |
| Segment diversity (age, income stability, source of money, influencer) | **High.** Students, first-jobbers, tier-2/3 users, gig workers. | Narrow | Narrow, higher income |
| Room for Growth-team levers that respect the constraints | High. Large, diverse base, many touchpoints (autopay, SIP dashboard, notifications). | Low. Zerodha's stated "no nudges" philosophy limits growth levers. | Medium |
| Ease of recruiting interviewees | **Easiest.** Most college / early-career SIP starters in my network will be on Groww. | Hard | Hard |

**The strategic signal.** Groww has about **44% of new SIP registrations** but about **14% of industry SIP inflows**. Part of that gap is small ticket sizes. Part could be continuation leakage. Either way, the 12-month continuation metric matters most at the platform that onboards the most first-timers. I'll use this as the "why this matters" hook on the deck. I must state it as a hypothesis, because I cannot separate ticket size from churn using public data.

---

## 2. End-to-end flow and how the deck maps to it

```
Business metric ─► Decomposition (Part 2) ─► AI Discovery Engine (Part 1) ─► Opportunity scoring
      ─► Pick segment + opportunity ─► 5–6 interviews (Part 3) ─► Problem definition (Part 4)
      ─► MVP + evals (Part 5) ─► 3 user tests (Part 6) ─► Metrics (Part 7) ─► Risks (Part 8)
```

**Proposed 10-slide deck. Every title states the slide's message.**
1. Title + one-line thesis
2. Metric decomposition: "12-month continuation leaks at X and Y, not only at market dips"
3. Discovery engine: how it works (the required 1-slide explanation + link)
4. Discovery findings: top opportunity areas, quantified and compared by segment
5. User research: what the interviews confirmed and what they overturned
6. Target segment + moment + root cause (the problem statement)
7. Solution rationale: why this, why AI earns its place, what a non-AI version would miss
8. MVP + eval results + user-testing learnings (link to the live MVP)
9. Success metrics: North Star → leading indicators → guardrails → AI quality
10. Risks, limitations and mitigations

---

## 3. Part 2 first: draft metric decomposition

I'll draft this **before** building the engine so the engine tags data against it. Then I'll revise it with the evidence.

```
12-mo active-SIP rate (first-time MF investors, cohort by first-SIP month)
│
├── A. SIP gets properly "live" (Month 0–1)
│     ├─ Autopay/mandate registration success rate & time-to-activate
│     ├─ First instalment success rate
│     └─ Users who start with a one-time payment but never set up autopay
│
├── B. Instalments keep succeeding  ── INVOLUNTARY lapse
│     ├─ Debit-date vs salary/cash-flow mismatch → insufficient balance
│     ├─ Mandate expiry / bank account change / UPI-autopay limits
│     ├─ Failure communication & retry/recovery (does the user even know it failed?)
│     └─ Consecutive failures → SIP auto-cancelled by the AMC/RTA
│
├── C. User chooses to keep going  ── VOLUNTARY lapse
│     ├─ Pause rate, and pause → resume rate (does pausing quietly become stopping?)
│     ├─ Reduce-amount vs stop (a softer exit is better for the metric than a full stop)
│     ├─ Stop/cancel rate by month (M1–M3, M4–M6, M7–M12)
│     ├─ Redeem-and-stop (liquidity need, goal reached, "it's not working")
│     └─ Drivers: expectation gap · reading returns · income shock · lack of a goal ·
│                 confusion/trust · peer/influencer advice · too many SIPs
│
├── D. Re-entry / substitution
│     ├─ Restart after a stop (re-activation within the window)
│     └─ Switch to a different SIP (counts as retained)
│
└── Engagement behaviours (diagnostic, not the goal)
      ├─ Check frequency & what's checked (returns %, current value, XIRR, NAV)
      ├─ Goal linked / not linked
      └─ Notification & statement engagement
```

**Product outcomes to name explicitly:** mandate success rate, instalment success rate, pause → resume rate, M3/M6 survival, % "stop intents" that end in a softer alternative the user picks freely, and restart rate.

---

## 4. Part 1: AI Discovery Engine (the biggest technical block)

### 4.1 Recommended stack (fast and free or cheap)
- **Collection:** Python scripts
  - Play Store: `google-play-scraper` (Groww app, sort by newest + most relevant, filter for SIP keywords)
  - App Store: Apple RSS customer-reviews feed (India storefront, ~500 most recent)
  - Reddit: public `.json` endpoints or PRAW. Subs: r/IndiaInvestments, r/mutualfunds, r/personalfinanceindia, r/IndianStreetBets (search "SIP stop", "pause SIP", "first SIP", "Groww SIP")
  - TradingQ&A: a Discourse forum, so `/search.json?q=sip` works
  - YouTube: Data API v3 (free key). Comments on 10–15 popular Hindi/English "SIP for beginners" / "should I stop my SIP" videos
  - X / Instagram: skip or add a small manual sample. Note this as a limitation.
- **Analysis:** LLM API (Claude, or Gemini/Groq free tier if budget is a problem) with structured-JSON extraction
- **Storage:** CSV/Parquet + a Google Sheet export for transparency
- **Front end / testable link:** **Streamlit** on Streamlit Community Cloud or Hugging Face Spaces
  - Tab 1: explore themes, counts, and segment cuts, with sample quotes
  - Tab 2: "Ask the corpus" Q&A over the data, answered with citations
  - Tab 3: "Analyse new text". Paste reviews and see live tagging. This shows the workflow working, not just its results.
- *Alternative:* n8n/Zapier for orchestration. More visual, but slower to build and harder to quantify. Only use it if I'm not comfortable with Python.

### 4.2 Pipeline
1. **Gather** → raw items with source, date, URL, and rating (target volumes below)
2. **Clean** → dedupe, drop very short or non-English/Hindi items (or transliterate Hinglish), **strip PII**
3. **Relevance filter** → keyword pre-filter, then an LLM check: "Is this about starting, continuing, pausing or stopping SIPs or first-time MF investing?" Most Play Store reviews are about KYC, app bugs and stocks, so most will be dropped. That's expected.
4. **Structured extraction**, one JSON per item:
   - `lifecycle_stage` (pre-start / month 0–1 / 2–6 / 7–12 / 12+ / unknown)
   - `action` (started / checking / considering pause / paused / reduced / stopped / redeemed / continued / restarted)
   - `trigger` (from the taxonomy: expectation gap, negative or flat returns, liquidity need, income change, mandate/payment failure, confusion about numbers, app/trust issue, peer/influencer, goal reached, no goal, too many SIPs, other)
   - `what_they_check`, `outside_app_behaviour` (YouTube, friends, Reddit, CA/advisor, family)
   - `emotion`, `unmet_need` (free text, then clustered)
   - `segment_signals`: age band, income type (salaried / student / gig / business), source of money, influencer. Only fill these when explicit, otherwise `unknown`.
   - `evidence_quote` (short span) + `confidence`
5. **Theme discovery** → embed `unmet_need` + `trigger` text, cluster, have the LLM name the clusters, then **I review and merge**. This is a deliberate human-correction point for the Evidence Log.
6. **Quantify** → share of relevant mentions per theme, by source, by lifecycle stage, and by segment where known
7. **Opportunity scoring.** Map each theme onto a decomposition node (§3) and score it:
   `Reach (share of mentions) × Metric impact (which node, how direct) × Confidence (agreement across sources) × Addressability (solvable without advice or fear)`
   This produces a ranked opportunity table, which is the main output of Part 1.
8. **Validate** → golden set (§4.4)

### 4.3 Target volumes (realistic for one weekend)
| Source | Raw | After relevance filter (est.) |
|---|---|---|
| Play Store | 5,000–10,000 | 300–800 |
| App Store | ~500 | 30–80 |
| Reddit posts + top comments | 800–1,500 | 300–600 |
| YouTube comments | 2,000–4,000 | 200–500 |
| TradingQ&A threads | 150–300 | 80–150 |
**Aim for a few thousand raw and ~1,000+ relevant items.** That's enough to quantify, and I'll report exact figures in the Evidence Log.

### 4.4 Validation and AI Evidence Log (start on day 1, not at the end)
- **Golden set:** ~20 items stratified across sources and themes. Include some hard cases: Hinglish, sarcasm, and complaints mixing app bugs with SIP issues. I label them by hand **before** looking at the AI labels.
- **Agreement:** % exact match on `trigger` and `action`, plus a confusion summary showing where the engine fails.
- **Rejected/corrected AI output (need 2–3):** I expect these naturally:
  - The LLM inventing segment info such as age or income when nothing was stated
  - Over-attributing stops to "market fall" when the real trigger was a cash-flow problem or a failed mandate
  - Merging distinct clusters (e.g. "returns confusion" vs "returns disappointment")
- **Log as I go:** prompt versions, what changed, and why.
- **Golden set doubles as the MVP eval set** (§7.3). Add 2 columns: `user_message_variant` and `expected_safe_behaviour`.

---

## 5. Choosing the segment and opportunity

I'll pick after the engine runs. **Current hypotheses to test, not conclusions:**

| # | Hypothesis | Decomp. node |
|---|---|---|
| H1 | **Expectation gap.** First-timers anchor on "12% a year" from calculators and YouTube. Months 2–6 look flat or negative. They can't read absolute return vs XIRR, conclude "it's not working", and pause or stop. | C |
| H2 | **Cash-flow mismatch.** The debit date doesn't match when money arrives (salary date, stipend, irregular gig income). Failures pile up and the SIP lapses silently, even though the user still intends to invest. | B |
| H3 | **Pause becomes stop.** Pause is a low-friction exit. The pause ends, but the user has mentally moved on or the next debit fails. | C/B |
| H4 | **No anchor.** The SIP was started on a friend's or influencer's suggestion with no personal goal. At the first liquidity need, it gets redeemed. | C |
| H5 | **Confusion that leads to inaction or exit.** Mandate status, missed-instalment notices, NAV/units, too many small SIPs. The user stops to "clean up". | B/C |

**Segment I expect to pick, if the evidence supports it:** *early-career first-time investors (≈21–27), first salary or stipend, started a SIP in the last 3–12 months, often after peer/YouTube influence.* Reasons: high volume in the data, highly recruitable from my network, and a strong expectation-gap and cash-flow story. **A fallback segment** is students and irregular-income users (H2 is sharper for them). This is a decision gate (§9).

---

## 6. Part 3: User research

**Method:** semi-structured, 30–40-min remote interviews (Meet or phone, Hindi/English) built on a **timeline walkthrough** ("take me from the day you started to today"). Use **critical-incident probing** on any moment they paused, reduced, or nearly stopped. Ask for **behaviour over opinion** ("last time you opened the app, what did you look at?"). No hypotheticals until the end.

**Sample (5–6):** all Groww first-time MF investors in the chosen segment, with a SIP started **3–15 months ago**. **Mix them on purpose:** ~3 who paused, stopped or seriously considered it, and ~2–3 who continued. The brief asks what separates the two groups, so I need both.

**Screener (a quick Google Form or WhatsApp questions):** age band · first MF investment? · platform · month the SIP started · income type · ever paused/stopped/reduced? · who suggested it. **Never ask for PAN, account numbers or screenshots.** I'll state this in the consent line.

**Discussion guide outline:**
1. Warm-up: work and money situation, in broad strokes
2. Why they started, who influenced them, and what they **expected** after 1 month, 6 months, a year
3. The experience since, month by month. Highs and lows.
4. Pausing, reducing or stopping: what happened, the moment itself, what they did next
5. Checking: what, how often, and how it **felt**. Ask them to show it in the app *verbally*, no screenshots.
6. Outside the app when unsure: who or what they consult
7. What would make them more likely to continue
8. Close: anything we didn't ask about

**Synthesis:** a quick affinity map by question × participant. For each AI-found theme, mark it as **Confirmed / Nuanced / Contradicted / New**. That table goes onto the "research challenged AI" slide.

**⚠️ Recruitment is the bottleneck. Send messages TONIGHT** (college groups, family, LinkedIn, workplace friends), and ask the same people now whether they'd do a 15-min MVP test on Sunday night or Monday morning.

---

## 7. Part 5: MVP (final design depends on the problem; this is the framework)

### 7.1 Shape
A **web prototype styled as a feature inside Groww's SIP journey**, deployed publicly. Candidate concepts by hypothesis:
- **H1 →** "SIP check-in explainer": the user pastes their own numbers (amount, months, current value, *typed by them, no screenshots*) or a question. The AI explains in plain language what they're seeing, how SIP returns typically behave early on (with general, non-fund-specific illustrations), and what XIRR means. It never says "stay" or "stop".
- **H2/H3 →** "Pause/stop intent helper": when a user taps Pause or Stop, a short conversation captures the reason and then neutrally lists **all** options (change date to match pay day, reduce amount, skip one instalment, pause, stop), with stopping kept just as easy. The AI classifies the reason and tailors which option to explain first.
- **H4 →** a goal-anchoring companion that helps users write down their own reason and horizon.

### 7.2 Where AI earns its place (and what a non-AI version misses)
Free-text reasons are messy, Hinglish, and emotional. Static FAQs and dropdowns miss the *actual* concern ("my friend said small caps are crashing", "salary got delayed this month"). AI's job is to **understand and route**, not to advise.

### 7.3 Eval gate (required)
```
User input ─► [Guard 1] Advice / out-of-scope classifier
                 ├─ "Which fund should I buy?", "Should I stop?" as a decision request ─► polite decline
                 │     + what I *can* explain + link to AMFI investor education / SEBI-registered advisor
                 └─ in scope ─► [Concern classifier — same taxonomy as discovery engine]
                                   └─ [Response generator, grounded in a small curated KB:
                                         AMFI / SEBI investor-education pages, Groww help articles]
                                         └─ [Guard 2] Output check: no fund names, no return promises,
                                               no fear/urgency language, cites a source; low confidence
                                               ─► "I'm not sure" + official source
UI always shows: "Educational only. Not investment advice."  + a visible "✓ Passed safety check" badge
```
**Measure against the golden set:** concern-classification accuracy, refusal precision/recall on advice-seeking items, guard-2 violation rate (target 0), and groundedness on a handful of manual checks. Report it as a small table on slide 8 and in the Evidence Log.

### 7.4 Build and deploy
Streamlit, or a simple Next.js/Vercel app if I'm comfortable with it. API key in secrets, a per-session message cap, and **no login**. Put 3 suggested prompts on screen so mentors can try a realistic task straight away.

---

## 8. Parts 6–8

**Part 6: user testing (≥3, the same segment, ideally from the interviewee pool).** Give each a **real task**, e.g. "your SIP looks lower than you expected this month, use this to understand what's going on" or "you're thinking of pausing next month, go through it". Use think-aloud and record: task success, confusion points, trust ("would you believe this?"), and whether it felt like advice or pressure. Finish with a **"what I'd change in v2"** list.

**Part 7: metrics**
- **North Star:** 12-month active-SIP rate for first-time MF investors (monthly cohorts)
- **Leading:** M1/M3/M6 survival · instalment success rate · pause → resume rate · % of stop-intent sessions where the user *freely* picks a softer option · feature engagement in the target moment
- **Guardrails:** complaints about being "blocked" from stopping (the stop flow must stay ≤ its current steps) · notification opt-outs · support tickets · redemption-delay complaints · any advice-like output (target 0) · CSAT
- **AI quality:** golden-set accuracy, refusal precision/recall, guard violation rate, fallback rate, latency
- Each metric gets: definition, formula, and rationale

**Part 8: risks** (specific to my solution once chosen). Likely candidates:
- Bias in public data: reviews skew to complaints, Reddit skews to experienced investors
- Small interview sample
- LLM gives something that reads like advice. Mitigation: guards + golden-set regression + human review.
- Regulatory perception: Groww is a distributor, so the feature must stay inside investor-education territory
- Seen as a dark pattern that retains users against their will. Mitigation: equal-effort stop, guardrail metric.
- Cannibalising "healthy" stops (a user who genuinely needs the money)
- Hinglish handling
- Cost and abuse on a public link

---

## 9. Timeline (≈65 hours, with decision gates)

| When | Work | Output / gate |
|---|---|---|
| **Fri 6 Nov, 11 PM–1 AM** | Read plan · **send recruitment + screener messages** · set up repo, API keys, Streamlit account · draft decomposition v1 · start Evidence Log doc (Google Doc, "anyone with link" view) | Recruits pinged ✅ |
| **Sat 7 Nov, 8 AM–1 PM** | Scrapers for all sources → raw data · cleaning + relevance filter · taxonomy v1 · label golden set (20) *before* running extraction | Raw + filtered dataset |
| **Sat 7 Nov, 1–6 PM** | Run extraction · cluster themes · human merge/correct (log it) · quantify · opportunity scoring · golden-set agreement | **GATE 1 (6 PM): choose segment + opportunity** |
| **Sat 7 Nov, 6–11 PM** | Finalise discussion guide · **interviews 1–3** · deploy the engine to Streamlit (v1 link) | 3 interviews done |
| **Sun 8 Nov, 9 AM–1 PM** | **Interviews 4–6** · synthesis: Confirmed / Nuanced / Contradicted / New | **GATE 2 (1 PM): lock problem statement** |
| **Sun 8 Nov, 1–10 PM** | MVP build → guards → KB → eval vs golden set → iterate prompts → **deploy** | **GATE 3 (10 PM): public MVP link works on a phone** |
| **Sun 8 Nov, 10 PM–12 AM** | User tests 1–2 (if available) | |
| **Mon 9 Nov, 7–10 AM** | User test 3 · write metrics + risks · finish Evidence Log | |
| **Mon 9 Nov, 10 AM–1 PM** | Build the 10-slide deck · check fonts/colour/links (open each link in incognito) · export PDF `NL_Groww` | **Submit by 1 PM** (≈3 hr buffer) |

**If I fall behind:**
- Cut YouTube or App Store sources first.
- Ship the engine as a static dashboard plus the "analyse new text" box.
- Narrow the MVP to one flow with the guards.
- Never cut the golden set, the evals, or the public deploy. Those are explicitly graded.

---

## 10. Deliverables checklist
- [ ] **Discovery Engine link** (testable) + 1 deck slide explaining it
- [ ] **AI Evidence Log** (one doc, public view): sources and volumes · golden set (~20) with agreement % and failures · 2–3 rejected/corrected AI outputs with reasons · MVP eval results
- [ ] **Deployed MVP link** (public, no login, disclaimer visible, quality-check/fallback visible)
- [ ] **PDF deck**: ≤10 slides, message-style titles, font ≥14, colour-blind-safe palette, no Fellow name, all links accessible, <40 MB, named `NL_Groww`
- [ ] Interview notes (anonymised) + screener + test notes linked from the deck

## 11. Open decisions for me before starting
1. **Coding comfort:** Python + Streamlit (recommended) or no-code (n8n)?
2. **LLM budget:** a paid API key, or free tiers only (Gemini/Groq)?
3. **Recruiting reach:** can I realistically get 5–6 Groww first-timers by Saturday evening? If not, broaden the segment definition now.
4. **Confirm Groww** (recommended above).
