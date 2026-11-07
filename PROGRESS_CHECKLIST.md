# Progress Checklist: Groww SIP Continuation

**Deadline:** Mon 9 Nov 2026, 3:59 PM IST · **Target:** submit by 1:00 PM
**Last verified:** Sat 7 Nov 2026, checked against the actual files (not from memory).

Legend: `[x]` done and checked · `[ ]` not done · **👤 You** = only you can do it · ❓ = I can't see this from here, tick it yourself if done

## Summary

| Step | What | Plan time | Done |
|---|---|---|---|
| 1 | Setup + recruitment | Fri night | 8 / 11 |
| 2 | Metric decomposition + taxonomy | Fri night | **3 / 3 ✅** |
| 3 | Collect + clean data | Sat 8–11 AM | 7 / 8 |
| 4 | Hand-label golden set | Sat 11 AM–12 PM | **4 / 4 ✅** |
| 5 | AI analysis → ranked opportunities | Sat 12–6 PM | **10 / 10 ✅** |
| 6 | Deploy Discovery Engine link | Sat 6–7 PM | 4 / 8 |
| 7 | 5–6 interviews + synthesis | Sat 7 PM – Sun 1 PM | 2 / 6 |
| 8 | Problem definition | Sun 1–2 PM | 0 / 3 |
| 9 | MVP + eval + 3 user tests | Sun 2 PM – Mon 10 AM | 2 / 12 |
| 10 | Metrics, risks, deck → submit | Mon 9 AM–1 PM | 0 / 7 |
| | **Total** | | **40 / 72** |

**⏰ Reminder (you asked):** review the golden-set labels in `data/golden_set.xlsx` and change any you disagree with. Do it before the Step 9 MVP eval, which reuses them. Then I'll re-run `python step5_validate.py`.

**Blocking right now:**

---

## Step 1: Setup + recruitment
- [x] Recruitment done: participants are ready for interviews and forms (confirmed by you, 7 Nov)
- [ ] 👤 Create the GitHub repo. *A local git repo exists, but with 0 commits and no remote. `gh` isn't installed, so create it on github.com.*
- [ ] 👤 ❓ Create a Streamlit Community Cloud account
- [x] Gemini key works: bulk `gemini-3.5-flash-lite` + quality `gemini-3.5-flash`. *3.7/3.8 Flash kept returning 503 "overloaded", so I switched.*
- [x] Groq backup key works: `openai/gpt-oss-120b`. *The old llama model was retired.*
- [x] YouTube Data API key works
- [x] Google Play scraping works (no key needed)
- [x] Reddit (optional): tried, but it's blocked without API keys, so skipped and noted as a limitation
- [x] Python libraries installed in `.venv` (`requirements.txt`)
- [x] Keys only in `.env`, which git ignores. `.env.example` has blank keys, and no file git would commit contains a key.
- [ ] 👤 Create the AI Evidence Log Google Doc (share: anyone with link → viewer), then paste in [evidence_log.md](evidence_log.md)

## Step 2: Metric decomposition + taxonomy ✅
- [x] Decomposition tree: A. SIP goes live · B. involuntary lapse · C. voluntary lapse · D. re-entry/switch · E. engagement → [step2_decomposition.md](step2_decomposition.md)
- [x] Product outcomes named (mandate success, instalment success, pause → resume, M3/M6 survival, restart rate…)
- [x] Taxonomy (tag list): 6 stages · 12 actions · 15 triggers · 4 segment signals → [taxonomy.py](taxonomy.py) (shared by the engine and the MVP)

## Step 3: Collect + clean data
- [x] Play Store: 9,796 raw → **743** relevant
- [x] App Store: 500 raw (Apple's feed limit) → **28**
- [x] Reddit: attempted, blocked (403), skipped as a limitation
- [x] YouTube: 15 SIP videos, 1,568 comments → **492**
- [x] TradingQ&A: 200 threads, 1,745 posts → **974**
- [x] Clean + filter (dedupe, remove PII, drop short items, keep SIP-related) → **2,237 items** in [data/filtered_data.csv](data/filtered_data.csv). The target was 1,000+.
- [x] Source-wise counts (raw and filtered) written up: [evidence_log.md](evidence_log.md) §2 and [step3_data_summary.md](step3_data_summary.md)
- [ ] 👤 Paste the counts into the Evidence Log Google Doc

## Step 4: Golden set ⚠️
- [x] 24 items picked by keyword rules only (no AI): 11 Play Store, 6 YouTube, 5 TradingQ&A, 2 App Store. Includes Hinglish, mixed bug + SIP and 2 off-topic items → [data/golden_set.xlsx](data/golden_set.xlsx)
- [x] Extra columns for the MVP eval: `user_message_variant`, `expected_safe_behaviour` (all labels have dropdowns, plus a how-to tab)
- [x] Labels for all 24 items: *drafted by Claude from the text only, reviewed by you (0 changes)*
- [x] Labelled without looking at the engine's labels

## Step 5: AI analysis → ranked opportunities
- [x] Extraction: all 2,237 items tagged by Gemini (batches of 20, saved after each) → **1,856 relevant**. 0 missing, 0 duplicates.
- [x] Automatic checks: every value checked against the taxonomy, with 47 wrong-field values repaired. **96.1%** of evidence quotes are exact copies of the text; the rest are flagged and never shown.
- [x] Themes proposed by the AI: 12 → [data/themes_ai_v1.json](data/themes_ai_v1.json) (kept unchanged as the original)
- [x] Themes reviewed and corrected: 1 split, 3 branch fixes, 2 addressability fixes → 13 themes in [data/themes.json](data/themes.json)
- [x] AI corrections logged (2–3 needed, **5 logged**) → [evidence_log.md](evidence_log.md) §5
- [x] Quantified: % per theme by source, lifecycle stage, action and segment → [data/theme_breakdowns.xlsx](data/theme_breakdowns.xlsx)
- [x] Ranked opportunity table (Reach × Impact × Confidence × Addressability) → [step5_results.md](step5_results.md), [data/opportunities.csv](data/opportunities.csv), Evidence Log §6
- [x] Golden-set agreement: relevance 79% · stage 83% · trigger 78% · action 39%, plus 6 failure patterns → Evidence Log §4
- [x] Decision gate: **payment failures** (node B) + segment (provisional) early-career first salary/stipend, first Groww SIP 3–15 months ago
- [x] Decision + reasons written in Evidence Log §9

## Step 6: Deploy the Discovery Engine link
- [x] Tab 1 Findings: ranked opportunities, stop-triggers, lifecycle chart, payment-failure deep dive, theme explorer with verified quotes → [streamlit_app.py](streamlit_app.py)
- [x] Tab 2 Ask the data: tag-based retrieval + dataset-wide counts, cited answers, citation + quote checks, the brief's 9 questions preloaded
- [x] Tab 3 Analyse new text: live tagging with the same prompt/taxonomy/validation (Hinglish tested)
- [ ] Push code to GitHub (first commit; `.env` stays out)
- [x] Tab 4 How it works & validation: pipeline diagram, sources, golden-set agreement, failure patterns, AI corrections, limitations
- [ ] Deploy on Streamlit Cloud with API keys in **Secrets**, not in code
- [x] Usage cap: 12 AI calls per session, 250 per day, answers cached
- [ ] Open the link in incognito and on your phone: it must work without logging in. *(Tested locally on desktop + phone size ✅; re-check after deploy.)*

## Step 7: User interviews (5–6) + synthesis
- [x] 👤 Recruited (confirmed by you). *Check that each one fits: first Groww SIP 3–15 months ago, early-career/stipend.*
- [ ] 👤 Mix: ~3 who paused, stopped or considered it + ~2–3 who continued
- [x] Interview guide focused on payment failures: 5 hypotheses, ~35-min script, notes + synthesis templates → [step7_interview_kit.md](step7_interview_kit.md). Screener Q10b added to `recruitment_kit.md`.
- [ ] 👤 Run the interviews (30–40 min each)
- [ ] 👤 Anonymised notes
- [ ] Synthesis: each AI theme marked Confirmed / Nuanced / Contradicted / New → Evidence Log §7

## Step 8: Define the problem
- [ ] One-paragraph problem statement: segment · moment in the first 12 months · product outcome · **root cause** · current workarounds · user value · business value
- [ ] Evolution story: Metric → Outcomes → AI findings → Interviews → Problem (including what the interviews **changed**)
- [ ] Check it avoids the "people stop when markets fall" framing *(our data already supports this: market fall is only 7% of mentions)*

## Step 9: MVP + eval + user tests
- [x] Gemini → Groq automatic backup, ready to reuse → [llm.py](llm.py)
- [x] Same taxonomy available for the concern classifier → [taxonomy.py](taxonomy.py)
- [ ] Guard 1: advice detector ("Which fund?", "Should I stop?") → polite decline + AMFI / SEBI-registered-advisor pointer
- [ ] Concern classifier (uses the taxonomy)
- [ ] Small knowledge base from AMFI, SEBI and Groww help pages
- [ ] Grounded answers from that knowledge base
- [ ] Guard 2: output check (no fund names, no return promises, no fear/urgency words). If it fails or confidence is low → "Not sure" + official link.
- [ ] Always visible: "Educational only. Not investment advice." + "✓ Safety check passed" badge
- [ ] Eval on the golden set: classification accuracy · refusal precision/recall · violation rate → Evidence Log §8
- [ ] Deploy: public, no login, 3 example prompts on screen
- [ ] 👤 3 user tests: a real task + think-aloud
- [ ] Test notes: what worked, what confused them, what to change in v2

## Step 10: Metrics, risks, deck → submit
- [ ] Metrics: North Star → leading indicators → guardrails (incl. "stopping must stay as easy as today") → AI quality, each with a definition + rationale
- [ ] Solution-specific risks, each with a mitigation
- [ ] Evidence Log final check: sources + volumes · golden set + agreement % · AI corrections · MVP eval
- [ ] 10-slide deck in Google Slides: message-style titles, font ≥14, colour-blind-safe colours, **no name anywhere**, links clickable
- [ ] Export as `NL_Groww.pdf` (<40 MB)
- [ ] Test every link in incognito
- [ ] 👤 **Submit** by 1 PM Mon 9 Nov

---

## "Never cut" items (graded explicitly)
| Item | Status |
|---|---|
| Golden set + agreement % | ✅ done (AI-drafted labels, disclosed) |
| AI corrections log | ✅ 5 logged |
| Eval-gated MVP with visible fallback | ❌ Step 9 |
| Public working links (engine + MVP) | ❌ Steps 6 and 9 |
| AI-vs-interview comparison | ❌ Step 7 |

## Checks already run
- `python test_keys.py`: all 5 required checks pass
- No API key in any file git would commit; `.env`, `.venv`, `data/raw/`, `data/logs/` are ignored
- PII scan of the filtered data: no phone numbers or PAN; emails, URLs, usernames and long numbers are replaced with tags
- Extraction: 2,237 / 2,237 tagged, 0 failed batches, 0 duplicates
- Theme assignment: 1,856 / 1,856 relevant items assigned (534 marked "no signal")
