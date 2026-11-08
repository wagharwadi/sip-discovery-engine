# Progress Checklist: Groww SIP Continuation

**Deadline:** Mon 9 Nov 2026, 3:59 PM IST · **Target:** submit by 1:00 PM
**Last verified:** Sat 7 Nov 2026, checked against the actual files (not from memory).

Legend: `[x]` done and checked · `[ ]` not done · **👤 You** = only you can do it · ❓ = I can't see this from here, tick it yourself if done

## Summary

| Step | What | Plan time | Done |
|---|---|---|---|
| 1 | Setup + recruitment | Fri night | 10 / 11 |
| 2 | Metric decomposition + taxonomy | Fri night | **3 / 3 ✅** |
| 3 | Collect + clean data | Sat 8–11 AM | 7 / 8 |
| 4 | Hand-label golden set | Sat 11 AM–12 PM | **4 / 4 ✅** |
| 5 | AI analysis → ranked opportunities | Sat 12–6 PM | **10 / 10 ✅** |
| 6 | Deploy Discovery Engine link | Sat 6–7 PM | **8 / 8 ✅** |
| 7 | 5–6 interviews + survey + synthesis | Sat 7 PM – Sun 1 PM | **8 / 8 ✅** |
| 8 | Problem definition | Sun 1–2 PM | **3 / 3 ✅** |
| 9 | MVP + eval + 3 user tests | Sun 2 PM – Mon 10 AM | 10 / 13 |
| 10 | Metrics, risks, deck → submit | Mon 9 AM–1 PM | 0 / 7 |
| | **Total** | | **63 / 75** |

**⏰ Reminder (you asked):** review the golden-set labels in `data/golden_set.xlsx` and change any you disagree with. Do it before the Step 9 MVP eval, which reuses them. Then I'll re-run `python step5_validate.py`.

**Blocking right now:**

---

## Step 1: Setup + recruitment
- [x] Recruitment done: participants are ready for interviews and forms (confirmed by you, 7 Nov)
- [x] GitHub repo created and pushed: `wagharwadi/sip-discovery-engine`
- [x] Hosting account: not needed for Streamlit (its sign-in was blocked); Render account created and used instead
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
- [x] Pushed to GitHub: public repo `wagharwadi/sip-discovery-engine`, commit `6ad03c8`, 50 files, no secrets (verified)
- [x] Tab 4 How it works & validation: pipeline diagram, sources, golden-set agreement, failure patterns, AI corrections, limitations
- [x] Deployed on **Render** (free; Streamlit Cloud sign-in blocked, Hugging Face now paid) → https://sip-discovery-engine.onrender.com. Keys in Render environment variables, not in code.
- [x] Usage cap: 12 AI calls per session, 250 per day, answers cached
- [x] Live link tested without login, on desktop and phone size: all 4 tabs, live AI answer (checks passed) and live tagging work

## Step 7: User interviews (5–6) + synthesis
- [x] 👤 Recruited (confirmed by you). *Check that each one fits: first Groww SIP 3–15 months ago, early-career/stipend.*
- [x] Mix achieved: 4 with a failed payment (2 also paused), 1 considering stopping, 1 smooth
- [x] Interview script (simple, ~15 min): 7 questions + show the 3 ideas, notes table → [step7_interview_kit.md](step7_interview_kit.md); analysis tables → [step7_synthesis_template.md](step7_synthesis_template.md) → [step7_interview_kit.md](step7_interview_kit.md). Screener Q10b added to `recruitment_kit.md`.
- [x] Concept test added to the guide: 3 concept cards (payday SIP · failure rescue · skip-not-stop), rotated order, asks for their own idea first → [step7_concept_cards.md](step7_concept_cards.md)
- [x] Survey run: **10 responses** (7 Groww), below the 25 target, reported as a small sample
- [x] 6 interviews done (P1–P6), run by a research assistant with the script
- [x] Anonymised notes (P-codes) → `interview_answers/` · ❗ check quotes against raw notes before the deck
- [x] Synthesis → [step7_synthesis.md](step7_synthesis.md) + Evidence Log §7: H2 timing failures confirmed (4/4), AI's "system-side" finding **contradicted**, ideas B 7 · A 4 · C 4

## Step 8: Define the problem
- [x] Problem statement (segment · moment · outcome · root cause · workarounds · user + business value) → [FINAL_SOLUTION.md](FINAL_SOLUTION.md) §1
- [x] Evolution story incl. what the interviews changed (AI said system faults → research showed cash-flow timing) → FINAL_SOLUTION.md §2
- [x] Avoids the "markets fell" framing: markets ~7% of complaints, 0 stops caused by markets in interviews

## Step 9: MVP + eval + user tests
- [x] Gemini → Groq automatic backup, ready to reuse → [llm.py](llm.py)
- [x] Same taxonomy available for the concern classifier → [taxonomy.py](taxonomy.py)
- [x] Guard 1: advice rules (English + Hinglish, prompt-injection) + router → polite decline + SEBI-registered-adviser link → [mvp_core.py](mvp_core.py)
- [x] Concern classifier (router, same taxonomy): payment failures 5/5, overall 50% vs golden labels
- [x] Knowledge base: 17 entries from Groww Help, Kotak MF, AMFI, SEBI, each with source link → [kb/sip_payments.json](kb/sip_payments.json)
- [x] Grounded answers: may use only the selected official entries, must cite them
- [x] Guard 2: no fund names / return figures / promises / fear words / advice phrasing, must cite a source; failure or low confidence → "Not sure" + official link
- [x] MVP app built → [rhythm_app.py](rhythm_app.py): setup in your own words · 6-month replay · monthly check-in · Lifelines · failure help · "How it's checked"; "not investment advice" always visible + "Safety check passed" badges
- [x] Eval on golden set + red-team (43 msgs, 3 iterations): **95% behaviour accuracy · refusal 100%/100% · 0 unsafe answers shown** → [mvp_eval.md](mvp_eval.md), Evidence Log §8
- [x] Rhythm SIP eval (46 labelled pay descriptions + replies, 2 iterations): v2 100% pattern / 100% reply intent / 100% date checks / 100% advice refusal → [rhythm_eval.md](rhythm_eval.md), Evidence Log §8b
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
| Eval-gated MVP with visible fallback | 🔶 core built + evaluated; user-facing feature after interviews |
| Public working links (engine + MVP) | ✅ engine live · ❌ MVP (Step 9) |
| AI-vs-interview comparison | ✅ Evidence Log §7 |

## Checks already run
- `python test_keys.py`: all 5 required checks pass
- No API key in any file git would commit; `.env`, `.venv`, `data/raw/`, `data/logs/` are ignored
- PII scan of the filtered data: no phone numbers or PAN; emails, URLs, usernames and long numbers are replaced with tags
- Extraction: 2,237 / 2,237 tagged, 0 failed batches, 0 duplicates
- Theme assignment: 1,856 / 1,856 relevant items assigned (534 marked "no signal")
