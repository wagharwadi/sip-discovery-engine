# Step 2: Metric Decomposition v1 + Taxonomy

**Metric:** 12-month active-SIP rate of first-time MF investors on Groww
= % of a first-SIP cohort that has **≥1 successful SIP instalment in the last 30 days**, 12 months after their first SIP.
Any active SIP counts (stopping SIP #1 but running SIP #2 = retained).

```
12-mo active-SIP rate (cohort by first-SIP month)
│
├── A. SIP goes live (Month 0–1)
│     ├─ Mandate/autopay registration success + time to activate
│     ├─ First-instalment success
│     └─ One-time payers who never set up autopay
│
├── B. Instalments keep succeeding ── INVOLUNTARY lapse
│     ├─ Debit date vs salary/cash-flow mismatch → insufficient balance
│     ├─ Mandate expiry / bank change / UPI-autopay limits
│     ├─ Does the user even know it failed? (failure comms, retry)
│     └─ Consecutive failures → SIP auto-cancelled
│
├── C. User chooses to keep going ── VOLUNTARY lapse
│     ├─ Pause rate, and pause → resume rate
│     ├─ Reduce amount vs full stop
│     ├─ Stop rate by month (M1–3, M4–6, M7–12)
│     ├─ Redeem-and-stop
│     └─ Drivers: expectation gap · reading returns · income shock · no goal ·
│                 confusion/trust · peer/influencer · too many SIPs
│
├── D. Re-entry / switching (counts as retained)
│     ├─ Restart after a stop
│     └─ Switch to a new SIP
│
└── E. Engagement (diagnostic, not the goal)
      ├─ What they check and how often (returns %, value, XIRR, NAV)
      ├─ Goal linked or not
      └─ Notification / statement engagement
```

**Product outcomes:** mandate success rate · instalment success rate · pause → resume rate · M3 / M6 survival · % of stop intents that end in a softer option the user picks freely (pause/reduce) · restart rate.

**Hypothesis to test (not assume):** a large share of lapse is *not* "markets fell". It is cash-flow timing (B) and expectation gap / confusing numbers (C) in months 2–6.

---

## Taxonomy (tag list used by the engine and the MVP)

Code version: [taxonomy.py](taxonomy.py). Import it, don't copy it.

| Field | Values |
|---|---|
| `lifecycle_stage` | pre_start · m0_1 · m2_6 · m7_12 · m12_plus · unknown |
| `action` | started · setup_failed · checking · considering_stop · paused · reduced · stopped · lapsed_involuntary · redeemed · continued · restarted · unknown |
| `trigger` | see below |
| `segment_signals` | age_band · income_type · source_of_money · influencer. **Only if explicitly stated**, else `unknown` |

| Trigger | Meaning | Node |
|---|---|---|
| expectation_gap | Returns lower/slower than expected | C |
| negative_returns | Portfolio red/flat, market fall | C |
| confusing_numbers | Doesn't understand XIRR / NAV / returns | C |
| liquidity_need | Needed the money | C |
| income_change | Job loss, salary delay, irregular income | C |
| payment_failure | Mandate/autopay failure, low balance, bank change | B |
| setup_friction | Trouble setting up mandate / first instalment | A |
| app_trust_issue | Bugs, wrong data, support, platform-safety doubts | C |
| peer_influence | Friend/YouTuber/Reddit/advisor said stop/switch | C |
| goal_reached | Goal done / horizon ended | C |
| no_goal | No clear reason, lost motivation | C |
| too_many_sips | Consolidating many SIPs | D |
| fund_switch | Moving to another fund (still investing) | D |
| other / none | Fits nothing / not stated | X |

**Tagging rules (to prevent known AI errors):**
1. Don't tag `negative_returns` just because someone stopped. If money wasn't there on the debit date, use `payment_failure` or `income_change`.
2. Never infer age or income from writing style.
3. `fund_switch` and `restarted` are **not** churn.

**MVP-only labels (golden set, Step 4):** `expected_safe_behaviour` = answer · decline_advice · not_sure_fallback.
