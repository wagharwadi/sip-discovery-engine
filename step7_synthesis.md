# Step 7 synthesis: interviews + survey (8 Nov)

**Sources**
- **6 interviews** (P1–P6), ~15 min each. Run by a research assistant using `step7_interview_kit.md`; notes formatted with AI help afterwards. *Verify any quote against the raw notes before using it in the deck.*
- **Survey:** 10 responses, 7 of them Groww users. The target was 25+, so it's a small convenience sample: read the counts as signals, not rates.

**Who we talked to**

| | Income | Payment ever failed? | Paused / stopped? | Idea picked |
|---|---|---|---|---|
| P1 | student (stipend) | yes | thought about reducing | **A** |
| P2 | first job | yes, found out 3 weeks later | thought about reducing | **B** |
| P3 | salaried 2+ yrs | no | no | **B** |
| P4 | freelance (irregular) | yes, twice | **paused, never restarted** | **C** |
| P5 | student (part-time) | no | thinking about stopping every month | **C** |
| P6 | first job | yes | **paused "for one month", it stayed paused 2 months** | **B** |

---

## Hypotheses: what held up

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | System failures (debited but no units, AutoPay bugs) break trust | **Nuanced** | None of the 4 failures was a system error; all were balance/timing. Trust *was* damaged, but by **how the app handled the failure** (silence, vague message, no retry), not by the failure itself (P2, P6, P1, P4). |
| H2 | Hidden failures: money leaves before the person's money arrives, and they blame themselves | **Confirmed (strongest)** | **4 of 4** interview failures were cash-flow timing: stipend late (P1), salary on the last working day + long weekend (P2), client hadn't paid (P4), salary "not cleared" by the debit (P6). Self-blame: P4 *"like I'm failing at this basic thing"*; survey: *"felt like I was doing something wrong"*. |
| H3 | People find out late or never | **Confirmed** | P2: 3 weeks later, by browsing the portfolio. P4: a week later in the app. P1: bank SMS 2 days later, nothing from Groww. P6: a Groww notification with no reason. Survey: **3 of 6** Groww failures were found out later. |
| H4 | After a failure the way back is unclear, so one failure becomes a stopped SIP | **Confirmed** | P1 googled and did nothing. P2 looked for "retry" and found none. P6 called the bank. P4 paused after the 2nd failure and never restarted. Survey: 1 person stopped after 2 failures. |
| H5 | People who keep going have a habit or buffer | **Confirmed** | P3 chose a date 6 days after salary, keeps a ₹15k minimum balance and has a calendar reminder. P5 chose a date 8 days after payday. Neither has had a failure. |

**New, which the AI could not see:**
1. **The SIP date was a default.** 3 of the 4 people whose payment failed never chose their date: *"the app suggested it"* (P1), *"the app defaulted to 1st"* (P2), *"I just clicked through"* (P6). Groww debits **one working day before** the SIP date (Groww Help), so a default date near payday is built to fail.
2. **Costly workarounds:** extra buffers of ₹3k (P2) and ₹5k in a second bank account (P6), checking the balance every month on the 4th (P1), calendar reminders (P3).
3. **An open-ended pause becomes a quiet stop:** P4 and P6 each lost 2 months. Both wanted to skip *one* month, but saw only "pause" or "stop". *(Groww's help describes Edit SIP → Skip Installment, so the option exists but these users didn't find it. Check in the app.)*
4. **Irregular income feels excluded:** P4's freelancer friends say *"SIP is for salaried people"*.

---

## Survey (Groww, n = 7)
| Question | Result |
|---|---|
| Ever had a failed instalment | **6 of 7** |
| ...and found out later | **3 of 6** (2 by noticing it in their portfolio) |
| SIP date **before** money arrives, or **0–2 days after** | **5 of the 6** failures; the 6th has income that varies month to month |
| After the failure | 3 went through next month by itself · 1 retried · 1 changed date · 1 paused/skipped · **1 stopped** |
| Idea picked | **B 3 · A 2 · C 2** |

*Across all 10 respondents, the 2 people whose SIP date is 3+ days after their money arrives never had a failure.*

## Idea test (interviews + survey, n = 16)
| Idea | Interviews | Survey | Total | Why people picked it |
|---|---|---|---|---|
| **B: When an instalment fails** | 3 | 4 | **7** | *"When things go wrong, that's when you lose trust"* (P2) |
| A: My payday SIP | 1 | 3 | 4 | *"If the date was right from day one, my payment wouldn't have failed. That's the root cause"* (P1) |
| C: Skip, not stop | 2 | 2 | 4 | *"If I could have just skipped that one month, I'd still be investing today"* (P4) |
| None | 0 | 1 | 1 | *"The key is keeping a buffer"* |

**Reading it:** people **choose B** because the failure moment is where trust breaks. But **A removes the cause**, and **C keeps people investing through a tight month**. B is the moment to act; A and C are the fixes it should offer.

---

## AI findings vs research (→ Evidence Log §7)
| AI finding (public reviews) | Research says | Evidence |
|---|---|---|
| Payment failures cluster in months 2–6 | **Nuanced** | Failures and pauses happened in the first ~7 months (P2 ~month 3–4, P6 pause in month 7), but the exact months weren't recorded for everyone |
| Failures are mostly system-side, not low balance | **Contradicted** | 4/4 interview failures and the survey comments are cash-flow timing. Public reviews over-represent system faults because **self-blamed failures never get reviewed**. |
| A bad payment experience → distrust → switch app | **Nuanced** | Distrust, yes. But nobody switched apps: they built workarounds or paused. |
| Support doesn't resolve payment problems | **Nuanced** | The gap isn't support tickets; it's missing **self-serve** information (no reason, no retry, generic help articles) |
| Markets are a minor reason for stopping | **Confirmed** | Returns cause anxiety (P2 *"felt sick"*, P5 *"rollercoaster"*), but **no pause or stop was caused by markets**. All came from cash flow. |
| People want pause/skip/modify instead of cancel | **Confirmed** | P4, P5 and P6 wanted to skip one month; the open-ended pause led to quiet drop-off |
| *(not seen by AI)* Default SIP date vs payday | **New** | 3 of 4 failures had a date the user never chose |
| *(not seen by AI)* Costly workarounds | **New** | Buffers, second accounts, reminders |

## What separates people who continue from those who drop off
People who keep going **chose a SIP date well after their money arrives and keep a buffer** (P3, P5). People who struggle **got a default date close to or before payday** (P1, P2, P6) or have **irregular income** (P4). After the first failure they get **no reason and no clear way back**, so they either carry the worry themselves (buffers, reminders) or **pause, and the open-ended pause becomes a stop** (P4, P6, survey R8).

## What the interviews changed
1. **Root cause:** from "system/payment-rail failures" (AI) to **a SIP date that doesn't fit when money arrives**: often a default, made worse by the one-day-early debit.
2. **Where trust breaks:** not at the failure itself, but in the **silence and missing recovery path after it**.
3. **Segment, sharpened:** from "early-career first-timers" to **first-timers whose money arrives late, on the last working day, or irregularly**: stipends, first salaries, freelance income (5 of 6 interviewees).
4. **Solution direction:** from three separate ideas to **one flow**. At the failure (or just before it), explain what happened and offer the fixes: **move the date after payday (A)**, **retry**, **skip just this month (C)**, with stopping as an equal option.
