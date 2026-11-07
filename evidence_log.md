# AI Evidence Log: Groww SIP Continuation (First-time Investors)

*Educational student project. No user financial or identity data was collected.*
*Draft kept in the project folder; paste each section into the shared Google Doc.*

## 1. Overview
- **Business goal being investigated:** raise the 12-month active-SIP rate of first-time mutual fund investors on Groww (active = ≥1 successful SIP instalment in the last 30 days; any SIP counts).
- Discovery engine link: [add after Step 6]
- MVP link: [add after Step 9]
- **Stack:** Python · Gemini API free tier (`gemini-3.5-flash-lite` for bulk tagging, `gemini-3.5-flash` for small quality runs) · Groq `openai/gpt-oss-120b` as automatic backup · Streamlit

## 2. Sources and volume analysed
Collected 6 Nov 2026.

| Source | How collected | Date range | Raw items | After relevance filter | Notes / limitations |
|---|---|---|---|---|---|
| Google Play reviews | `google-play-scraper`, Groww app, newest + most relevant (5,000 each, deduped) | 2018 – Nov 2026 | 9,796 | 743 | Most reviews are about stocks/KYC/bugs, so most are dropped (expected) |
| App Store reviews | Apple public RSS feed, India storefront | Sep – Nov 2026 | 500 | 28 | Feed returns only the latest ~500 reviews |
| Reddit | Public `.json` endpoints (no API keys) | – | 0 | 0 | **Blocked (HTTP 403)** without API keys. Skipped |
| YouTube comments | YouTube Data API v3: 15 popular Hindi/English SIP videos, top 300 comments each | 2019 – Nov 2026 | 1,568 | 492 | Many Hinglish comments |
| TradingQ&A | Discourse search API: 200 SIP threads, up to 20 posts each | 2017 – Oct 2026 | 1,745 | 974 | Zerodha community, so it skews to experienced, non-Groww users |
| **Total** | | | **13,609** | **2,237** | |

**After LLM relevance check (Step 5):** 1,856 of 2,237 items judged relevant (83%).

## 3. Pipeline and prompts
- **Cleaning and filtering:** exact-text dedupe → PII removal (URLs, emails/UPI IDs, phone numbers, PAN, 9–18 digit numbers, @/u/ usernames, forum quote blocks; author names never saved) → drop items under 30 characters or 6 words → SIP keyword filter (English + Hindi/Hinglish; for forum/YouTube comments, the thread title counts as context) → LLM relevance check.
- **Taxonomy:** `taxonomy.py`. 6 lifecycle stages, 12 actions, 15 triggers, 4 segment signals (only when explicitly stated). Every trigger maps to a decomposition node: A = SIP goes live, B = involuntary lapse, C = voluntary lapse, D = re-entry/switch, E = engagement.
- **Prompt versions:**
  - `extract_v1` (7 Nov): batches of 20 items, JSON output, taxonomy pasted into the prompt, explicit rules: "don't tag negative_returns just because they stopped", "fill segment only if stated", "copy an exact evidence quote".
- **Automatic checks on every AI output:**
  - Each value is validated against the taxonomy. Invalid values are logged, then either mapped to the value they clearly mean (synonym map) or set to unknown.
  - Each evidence quote is checked against the original text: **96.1%** of relevant items had an exact quote. The rest are flagged `quote_ok = false` and never shown as quotes.

## 4. Golden set (24 hand-labelled items)
24 items picked by keyword rules only (no AI), so the selection isn't biased toward the engine. They cover 10 themes plus hard cases: 2 Hinglish, 1 mixed app-bug + SIP issue, 2 deliberate off-topic items. Sources: 11 Play Store, 6 YouTube, 5 TradingQ&A, 2 App Store.

**How the labels were made:** an AI assistant (Claude) drafted the labels from the text only, without seeing the engine's (Gemini's) labels. I then reviewed all 24 and made no changes. So this checks one model against another, with human review on top. It is not a fully independent human labelling. Per-item comparison: `data/golden_agreement.csv`.

**Agreement (engine vs golden set):**

| Field | Agreement |
|---|---|
| is_relevant | **79%** (19/24) |
| lifecycle_stage | **83%** (15/18) |
| trigger (main field for themes) | **78%** (14/18) |
| action | **39%** (7/18) |
| segment info invented | 6 of 24 items |

*With only 24 items, each % is rough (about ±15–20 points).*

**Where the engine failed (patterns):**
1. **It assumes an action when none is stated** (7 of 11 action errors). It writes `started`/`continued` for people who are only asking questions, and `restarted` for people *asking* whether they can restart (yo_01987, tr_01393).
2. **It confuses "debited but no units allotted" as a setup failure (A) instead of an involuntary lapse (B)** (pl_00148, pl_00373).
3. **It over-includes generic praise as relevant** (4 of 5 relevance errors). This is mitigated: items with no need or trigger are kept out of theme shares (534 "no signal").
4. **It invents segment info, as predicted.** It tags YouTube commenters `influencer = youtube_social` just because they commented on YouTube (4 items), reads "salaried" into a job-seeker's review (pl_00180), and gives "pocket money" an age of <21 (yo_01842).
5. **It over-attributes to markets, as predicted:** "sitting on cash waiting for correction but also continuing SIPs" was tagged `negative_returns` (tr_01336).
6. Surprise: pl_00373 never uses the word "SIP" but is about failed autopay payments, so keyword filters can miss relevant items.

**What this means for the findings:**
- **Trigger and stage are reliable enough** (~80%) for the theme ranking.
- **Action-based numbers** ("lapse-action %") are directional only.
- **AI segment and influencer counts are NOT used as findings.** Segment comes from the interviews.

## 5. Where I rejected or corrected AI output (2–3)
| # | What the AI said | What I changed it to | Why | Effect on findings |
|---|---|---|---|---|
| 1 | Tagged 24 items' **action** as `fund_switch` (a *trigger* value, not an action), plus 23 other values using the wrong field's spelling (e.g. `lapsed_involuntary` as a trigger) | Mapped to the value each one clearly means: `fund_switch` → `restarted`, `lapsed_involuntary` → `payment_failure`, etc. (47 values) | The validator had forced them to "unknown", which lost real signal | Switchers now count as **retained (node D)** instead of unknown, which matters because the metric counts any active SIP |
| 2 | 3.9% of evidence quotes were not exact spans of the original text (paraphrased or invented) | Flagged `quote_ok = false`; excluded from all quote displays | Quotes shown to mentors must be real user words | No invented quotes in the deck or app |
| 3 | Theme "Portfolio Tracking and Return Display Discrepancies" merged two different problems: users not understanding XIRR/returns, and the app showing wrong/late data (NAV, balances) | Split into "Understanding Returns Numbers" and "Wrong or Delayed Portfolio Data"; re-assigned its 129 items (95 → data accuracy, 20 → returns comprehension, 14 → other themes) | Different root causes need different fixes (explanation vs data sync). This is the merge error I expected in advance | Returns confusion turned out much smaller (20 items) than the merged theme suggested |
| 4 | AI placed 3 themes in node E (engagement, impact 1): SIP mechanics/charges comprehension, customer support/reliability, redemption payouts | Moved all 3 to node C (voluntary lapse) | My decomposition lists confusion/trust as voluntary-lapse drivers, and `taxonomy.py` maps trust issues to C | "Comprehension of SIP Mechanics" rose from #4 to #2 (score 2.97 → 6.0) |
| 5 | AI addressability: "Negative returns" = 1 ("Groww can't control markets"); "Redemption payout delays" = 3 | Negative returns → 2; Redemption → 1 | Explaining what a dip means for a SIP is education, not advice. Faster payouts don't keep SIPs active, and slowing exits would be a dark pattern | Negative returns #9 → #6; Redemption stays low (#8) |

*Corrections 3–5: issues flagged during review with my coding assistant; I checked and approved each one. AI original: `data/themes_ai_v1.json`; reviewed version: `data/themes.json` (each change recorded in `review_changes`).*

## 6. Key findings (quantified)
1,856 relevant items. 1,322 carry an unmet need or trigger and are used for themes; 534 have no signal (e.g. "great app for SIP"). Themes v2 (after review).

**Score = Reach × Metric impact × Confidence × Addressability**
- Reach = mentions ÷ biggest theme
- Impact: A/B = 3, C = 2 (+1 if ≥50% of the theme's items are stop/pause/reduce/lapse), D/E = 1
- Confidence = share of the 4 sources where the theme is ≥3% of items
- Addressability (1–3) = fixable without advice or fear

| # | Theme | Node | Mentions | Lapse-action % | Groww-app share* | Score |
|---|---|---|---|---|---|---|
| 1 | Mandate setup and onboarding friction | A | 163 | 54% | 40% | **8.82** |
| 2 | Comprehension of SIP mechanics and charges | C | 166 | 21% | 12% | **6.00** |
| 3 | SIP flexibility (pause / skip / modify) | C | 164 | 49% | 22% | **5.94** |
| 4 | Involuntary payment failures and refunds | B | 139 | 76% | 59% | **5.67** |
| 5 | Wrong or delayed portfolio data | C | 95 | 18% | – | 2.56 |
| 6 | Negative returns / market downturn | C | 94 | 54% | – | 1.71 |
| 7 | Customer support / reliability | C | 82 | 43% | – | 1.47 |
| 8 | Redemption payout delays | C | 104 | 88% | – | 1.42 |
| 9–13 | Advanced features, fund switching, guidance requests (= advice, addr 1), other, returns comprehension | | | | | < 1 |

\*Share of the theme's items from Play Store + App Store reviews of the Groww app. The rest come from TradingQ&A (Zerodha community, more experienced users) and YouTube.

**Headline findings:**
- **"Markets fell" is a minor driver.** Negative returns are 7% of themed mentions and 6% of triggers behind stop/pause/lapse actions. Bigger triggers: app/trust issues 26%, payment failure 14%, setup friction 14%.
- **The top 4 are close (5.7–8.8).** Source matters: involuntary payment failure has the most Groww-specific evidence (59%), while "comprehension" is mostly TradingQ&A (58%).
- **Payment failures (chosen opportunity) are mostly system-side in public data.** Of 160 items (keyword-based, can overlap):
  - mandate/autopay failing 30%
  - support didn't resolve 27%
  - debited but no units / no refund 23%
  - bounce / insufficient balance 12%
  - double debit 8%
  - found out later 6%

  Only **7 of 160** mention salary or low balance. **Hypothesis:** balance-related failures are self-blamed and never reviewed, so they're invisible rather than rare. The interviews test this (H2 in `step7_interview_kit.md`).
- **Public data can't choose the segment or the month.** Income/age is stated in only ~3% of items, and the month in months 2–12 for only 58 items. Interviews must answer these.

Full table: `data/opportunities.csv`. Breakdowns by source / stage / action / segment: `data/theme_breakdowns.xlsx`.

## 7. AI discovery vs primary research
| AI theme | Interviews: Confirmed / Nuanced / Contradicted / New | Evidence |
|---|---|---|

## 8. MVP evaluation against golden set
| Metric | Result | Target |
|---|---|---|
| Concern classification accuracy | | |
| Advice-request refusal: precision / recall | | |
| Safety-check violations (fund names, return promises, fear words) | | 0 |
| Fallback rate | | |

## 9. Decision log (dated)
- **6 Nov:** chose Groww over Zerodha Coin and INDmoney: strongest first-timer fit (~44% of new SIP registrations, company figure), the most public data, and the easiest recruiting (see implementation plan §1).
- **6 Nov:** Groq retired `llama-3.3-70b-versatile`, so the backup model is now `openai/gpt-oss-120b`.
- **6 Nov:** Reddit blocked unauthenticated access (403). Skipped as a limitation rather than working around the block.
- **6 Nov:** found quoted usernames inside TradingQ&A posts. Changed the collector to drop quote blocks and re-collected.
- **6 Nov:** golden set picked by keyword rules, before any AI tagging. First pick had too many off-topic items, so every pick must now mention SIP, plus 2 deliberate off-topic items.
- **7 Nov:** `gemini-3.7-flash` and `gemini-3.8-flash` returned 503 "high demand" repeatedly, so the quality model is now `gemini-3.5-flash`.
- **7 Nov:** extraction ran as 3 parallel workers to stay within the free-tier limit (~10 requests/min) while finishing ~3× faster. Same prompt (`extract_v1`).
- **7 Nov:** 47 off-vocabulary AI values repaired with a synonym map (see §5 #1).
- **7 Nov:** themes v1 proposed by `gemini-3.5-flash` from 450 sampled unmet needs (12 themes). 534 relevant items with no need or trigger were kept out of theme shares rather than forced into "other".
- **7 Nov:** theme review → v2 (13 themes): 1 split, 3 node fixes, 2 addressability fixes (see §5 #3–5).
- **7 Nov: Decision gate 1.**
  - **Opportunity:** involuntary payment failures (node B: instalments that fail even though the user still wants to invest).
  - **Why:**
    - highest share of real lapses in its theme (~76%, directional given the 39% action agreement)
    - most Groww-specific evidence (59% from Groww app reviews)
    - concentrated in months 2–6, inside the 12-month window
    - fixable without advice or fear
    - avoids the "markets fell" framing
  - **Not chosen:**
    - mandate setup (highest score, but about *starting*, not continuing)
    - SIP flexibility (mostly app bugs, dark-pattern risk)
    - understanding SIPs (mostly TradingQ&A evidence, weak link to stopping)
  - **Segment (provisional):** early-career first-time investors (~21–27) on their first salary or stipend, first Groww SIP 3–15 months ago. Public data can't confirm the segment (income/age stated in ~3% of items), so the interviews will test it. Fallback: students / irregular-income users.
