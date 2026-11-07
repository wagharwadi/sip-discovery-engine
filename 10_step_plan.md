# 10-Step Execution Plan: Groww SIP Continuation (All-Free Stack)

**Deadline:** Mon 9 Nov 2026, 3:59 PM IST → **our target: submit by 1:00 PM**
**Rule:** finish each step's "Done when" before moving to the next one (steps 1 and 6 run in parallel with others).

**Free stack:** Python + VS Code · Gemini API (Google AI Studio, main model) · Groq (backup model) · google-play-scraper · Apple RSS reviews · PRAW (Reddit) · YouTube Data API v3 · GitHub · Streamlit Community Cloud · Google Docs / Forms / Meet / Slides

---

## Step 1: Setup + recruitment kick-off
**When:** Fri night (~1 hr)
- Send recruitment messages to college, family and work groups: *first SIP on Groww started 3–15 months ago, 30-min chat, no financial details asked.* In the same message, ask if they're free for a 15-min MVP test on Sun/Mon.
- Create free accounts and keys: GitHub, Google AI Studio (Gemini key), Groq key, Reddit script app, YouTube Data API key, Streamlit Cloud.
- Install Python libraries:
  `pip install -r requirements.txt` (google-play-scraper, praw, google-api-python-client, google-genai, groq, pandas, streamlit, python-dotenv, requests, openpyxl)
- Create the **AI Evidence Log** Google Doc (share: anyone with link → viewer) with empty sections.
- Create a project folder and GitHub repo. Keep keys in a `.env` file that is **never committed**.

**Done when:** messages sent, all keys working, Evidence Log doc exists.

---

## Step 2: Draft the metric decomposition (v1)
**When:** Fri night (~30 min)
- Break "12-month active SIP rate" into its branches:
  - **A. SIP goes live:** mandate/autopay setup, first instalment
  - **B. Instalments keep succeeding (involuntary lapse):** balance on debit date, mandate failure, bank change
  - **C. User chooses to continue (voluntary lapse):** pause, reduce, stop, redeem, and what drives each
  - **D. Re-entry / switching:** restart, or a new SIP (still counts as retained)
- Turn these branches into the **tag list (taxonomy)** the engine will use.

**Done when:** a one-page tree + taxonomy list exists. This is the v1 for deck slide 2.

---

## Step 3: Collect the data
**When:** Sat 8 AM–11 AM
- Run the collection scripts (Claude writes them, you run them on your laptop). Each one saves a CSV:
  - Play Store (5–10k reviews) · App Store (~500) · Reddit (r/IndiaInvestments, r/mutualfunds, r/personalfinanceindia) · YouTube comments (10–15 SIP videos) · TradingQ&A (SIP threads)
- Run the clean + filter script: dedupe, remove PII, drop very short items, keep SIP-related items.
- Record **source-wise counts** (raw and filtered) in the Evidence Log.

**Done when:** one combined `filtered_data.csv` with ~1,000+ relevant items.
**If stuck:** skip Reddit or YouTube and note it as a limitation.

---

## Step 4: Hand-label the golden set (before the AI runs)
**When:** Sat 11 AM–12 PM
- Pick ~20 items: a mix of sources and themes, plus a few hard ones (Hinglish, mixed complaints).
- Label each by hand: lifecycle stage, action, trigger, segment signals.
- Add 2 extra columns for later MVP testing: `user_message_variant` and `expected_safe_behaviour`.

**Done when:** golden set sheet is filled and saved, and **not yet compared** with AI output.

---

## Step 5: Run the AI analysis → ranked opportunities
**When:** Sat 12 PM–6 PM
- **Extraction:** Gemini tags every item in batches of 15–25 (structured JSON), saving after each batch.
- **Themes:** cluster the unmet needs and triggers, then **you review, merge and fix them**. Log every correction (you need 2–3 for the Evidence Log).
- **Quantify:** % of mentions per theme, by source, by lifecycle month, and by segment where it's known.
- **Score opportunities:** Reach × Metric impact × Confidence × Addressability (fixable without advice or fear).
- **Validate:** compare AI labels to the golden set, then record agreement % and failure cases.
- **Decision gate:** pick **one target segment + one moment/opportunity**.

**Done when:** ranked opportunity table + chosen segment, both written in the Evidence Log.

---

## Step 6: Deploy the Discovery Engine link
**When:** Sat 6 PM–7 PM (can run in parallel with interviews)
- Streamlit app with 3 tabs: **Themes dashboard** · **Ask the data (with quotes)** · **Analyse new text (live tagging)**.
- Push to GitHub, deploy on Streamlit Cloud, and put the API keys in **Secrets**, not in code.
- Open the link in incognito and on your phone.

**Done when:** a public link works without logging in.

---

## Step 7: User interviews (5–6) + synthesis
**When:** Sat 7 PM–11 PM (3 interviews) · Sun 9 AM–1 PM (2–3 interviews + synthesis)
- **Method:** semi-structured, 30–40 min, a timeline walkthrough from the day they started to today, plus deep-dives on any moment they paused, reduced or nearly stopped.
- **Mix:** ~3 who paused, stopped or considered it, and ~2–3 who continued.
- **Never ask for** PAN, account numbers or screenshots.
- **Synthesis:** for each AI theme, mark it **Confirmed / Nuanced / Contradicted / New**.

**Done when:** anonymised notes + the synthesis table exist.

---

## Step 8: Define the problem
**When:** Sun 1 PM–2 PM
- Write the problem statement: target segment · the moment in the first 12 months · the product outcome we're moving · **root cause** · current workarounds · user value · business value.
- Write out how the thinking evolved: Metric → Outcomes → AI findings → Interviews → Problem, including what the interviews **changed**.
- Avoid the framing *"people stop when markets fall."*

**Done when:** a one-paragraph problem statement + the evolution story exist.

---

## Step 9: Build, test and deploy the MVP + user tests
**When:** Sun 2 PM–10 PM (build) · Sun night / Mon 7–10 AM (3 user tests)
- **Streamlit app with Gemini** (Groq as automatic backup if Gemini hits its limit). Every user message passes through:
  1. **Guard 1:** advice detector. "Which fund?" or "Should I stop?" → polite decline + AMFI / SEBI-registered-advisor pointer.
  2. **Concern classifier:** same taxonomy as the engine.
  3. **Grounded answer:** from a small knowledge base built from AMFI, SEBI and Groww help pages.
  4. **Guard 2:** output check (no fund names, no return promises, no fear/urgency words). If the answer fails or confidence is low → "Not sure" + official link.
- Always show **"Educational only. Not investment advice."** and a visible **"✓ Safety check passed"** badge.
- **Eval:** run the golden set through the app, then record classification accuracy, refusal precision/recall and violation rate.
- **Deploy:** public, no login, 3 example prompts on screen.
- **User tests (3):** give each a real task with think-aloud. Note what worked, what confused them, and what to change in v2.

**Done when:** live MVP link + eval table + 3 test notes.

---

## Step 10: Metrics, risks, Evidence Log and deck → submit
**When:** Mon 9 AM–1 PM
- **Metrics:** North Star → leading indicators → guardrails (incl. "stopping must stay as easy as today") → AI quality metrics. Give each one a definition and rationale.
- **Risks:** solution-specific, each with a mitigation.
- **Evidence Log final check:** sources + volumes · golden set + agreement % + failures · 2–3 AI corrections · MVP eval results.
- **10-slide deck** in Google Slides: message-style titles, font ≥14, colour-blind-safe colours, **no name anywhere**, all links clickable and accessible.
- Export as `NL_Groww.pdf` (<40 MB), test every link in incognito, **submit**.

**Done when:** submitted before 1 PM (≈3 hr buffer before the 3:59 PM deadline).

---

### Never cut (graded explicitly)
Golden set + agreement % · AI corrections log · eval-gated MVP with visible fallback · public working links · the AI-vs-interview comparison

### Cut first if behind
YouTube / App Store sources → the "Ask the data" tab → MVP polish
