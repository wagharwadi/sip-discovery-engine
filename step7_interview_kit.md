# Step 7: Interview Kit (focus: SIP payment failures)

**Decision gate 1:** opportunity = involuntary payment failures (instalments that don't go through even though the user still wants to invest). Segment (provisional) = early-career first-time investors (~21–27), first salary or stipend, first Groww SIP 3–15 months ago.
**Sample (5–6):** ~3 who had a failed/missed instalment (or paused/stopped), ~2–3 whose SIP ran smoothly. Use screener Q10b in `recruitment_kit.md`.

---

## 1. What we need to learn (hypotheses to test, not to prove)

| # | Hypothesis | Why we think it | What would change our mind |
|---|---|---|---|
| H1 | **System failures break trust.** Money debited but no units, mandate/autopay failing, double debits → the user loses trust → stops or switches app | 53% of public payment-failure items are system-side (mandate 30%, debited-not-allotted 23%) | Failures were rare or quickly fixed, and trust wasn't affected |
| H2 | **Silent, self-blamed failures exist.** The balance is short on the debit date (debit date ≠ when money arrives), the user blames themselves, and nobody writes a review about it | Only 7 of 160 public items mention salary/low balance. **We think this is invisible, not absent.** | Nobody's debit date clashes with when their money arrives; no one remembers a balance-related failure |
| H3 | **People find out late.** The user doesn't notice a failure until days later (or never) | 6% say "found out later"; people who never found out can't write a review | Users notice immediately (SMS, app notification) |
| H4 | **Recovery is the real drop-off.** After a failure the path back is unclear (retry? wait? re-do the mandate?), so one failure quietly becomes a stopped SIP | Decomposition: consecutive failures → auto-cancel; "pause becomes stop" | The SIP carries on next month without the user doing anything, and users know it |
| H5 | **Continuers have a habit or buffer** (keep money aside, picked a date after salary, check the bank SMS) | The brief asks what separates continuers from stoppers | Continuers and stoppers behave the same way |

**AI findings to mark Confirmed / Nuanced / Contradicted / New** (for Evidence Log §7):
1. Payment failures cluster in months 2–6
2. Most payment failures are system-side, not low balance
3. One bad payment experience leads to distrust and switching platforms
4. Support doesn't resolve payment problems (27%)
5. "Markets fell" is a minor reason for stopping (7%)
6. Users want to pause, skip or modify instead of cancelling (SIP flexibility theme)

---

## 2. Before each call
- Calm setting, 35 min booked. Google Meet or phone, Hindi or English, whatever they prefer.
- Give them an ID (P1, P2…). **Never write their real name in the notes.**
- Recording only with explicit permission. Otherwise take notes live.
- Have the timeline sheet ready (section 5).

**Opening script (read it):**
> "Thanks for your time! I'm doing a student research project on how people experience their first SIP. There are no right or wrong answers. I'm not from Groww and I'm not selling anything. I will **never** ask for your PAN, account numbers, amounts, or screenshots. If anything feels too personal, just skip it. I may quote you anonymously. Is that okay? *(Can I record, just for my notes?)*"

---

## 3. Discussion guide (~35 min)

Ask the **bold** question, then use the probes only if needed. Ask about **behaviour, not opinions** ("what did you do", not "would you").

### A. Warm-up (3 min)
- **"Tell me a bit about what you do these days."**
- **"Roughly which part of the month does your money come in: salary, stipend, or family? Is it the same date every month?"** *(Only the timing, never amounts.)*
  - Hindi: *"Aapke paise mahine ke kis hisse mein aate hain? Har mahine same date ko?"*

### B. Starting the SIP (5 min)
- **"Take me back to when you started your first SIP. What made you start then?"**
  - Who suggested it? What did you expect after 6 months or a year?
- **"How did you set up the payment: autopay, UPI mandate, or paying each month yourself?"**
- **"How was the SIP date chosen? Do you remember?"** *(Key for H2. Did they choose it, or did the app default it?)*

### C. Timeline walkthrough (8 min)
- **"Walk me through it month by month, from the first instalment until today."** Fill in the timeline sheet together.
  - "Was there a month that felt different?" · "When did you last look at it?"

### D. Critical incident: payments (10 min) ⭐ the core of the interview
- **"Has there been a month when the SIP money didn't go through, or something odd happened with the payment?"**
  - Hindi: *"Kabhi aisa hua ki kisi mahine SIP ka paisa nahi kata, ya payment mein kuch gadbad hui?"*

**If YES, go slowly through what happened:**
1. "When was that? Which month of your SIP?"
2. **"How did you find out?"** (app notification / SMS / bank statement / noticed later / someone told you) · "How long after?" *(H3)*
3. **"What did you think had happened? Whose fault was it?"** *(The user's own balance or the app? This is H1 vs H2. Don't suggest an answer.)*
4. **"What did you do next: that day, and the next month?"** (nothing / retried / contacted support / added money / changed the date / paused / stopped)
5. If they contacted support: "How did that go?"
6. **"What happened to the SIP after that?"** Did it continue by itself? *(H4)* Did they know it would?
7. **"Did it change how you feel about the SIP, or the app?"** *(H1)*
8. "Did you change anything after that, like the date, the amount, or keeping money aside?"

**If NO:**
- **"How do you make sure the money is there on the SIP date?"** *(H5: buffer, date after salary, auto-transfer)*
- "Have you ever been close to not having enough on that date?"
- "If it did fail one month, what do you think would happen? What would you do?" *(tests H4 knowledge)*

**Everyone:**
- **"Have you ever paused, skipped, reduced, or thought about stopping the SIP?"** Then: what was happening at the time, and what you did.

### E. Checking and alerts (4 min)
- **"What happens on SIP day? Do you get any message, from the app or the bank?"**
- **"The last time you opened the app, what did you look at?"** *(Describe it; no screenshots.)*

### F. Outside the app (2 min)
- **"When you're unsure about something with your SIP, who or what do you check with?"** (friends, YouTube, family, customer care…)

### G. Close (3 min)
- **"If you could change one thing about how SIP payments work for you, what would it be?"** *(The only hypothetical; keep it for the end.)*
- "Anything I didn't ask that I should have?"
- **Ask about the MVP test:** "Would you try a 15-min prototype on Sun night or Mon morning?"
- Thank them.

### Interviewer rules
- **Don't lead.** ❌ "Was that frustrating?" ✅ "How did that feel?" · ❌ "Was it the app's fault?" ✅ "What do you think happened?"
- **Stay quiet for 3 seconds** after an answer; people usually add the important part.
- **"Tell me more about that"** and **"Can you give me an example?"** are your best probes.
- **Never give advice** (no "you should keep going"), even if they ask. Say: "I'm only here to learn, but I can share AMFI's investor education link afterwards."
- Never ask for amounts, PAN, account numbers or screenshots.

---

## 4. Notes template (one per participant)

```
ID: P_   Date/time:   Length:   Language:
Bucket: Failed-instalment / Paused / Stopped / Considered / Smooth
Segment: age band __ · income: student / first job / 2+ yrs / gig · money arrives: ~__ of month, fixed? Y/N
Started: ~__ months ago · Suggested by: __ · Payment method: autopay / UPI mandate / manual
SIP date chosen by: me / app default / don't remember

Payment incident: Y/N
  When (SIP month): __   Found out how/when: __
  Blamed: self / app / bank / unsure   What they did next: __
  Outcome: continued / paused / stopped / switched app   Trust change: __

Habits (buffer / date after salary / checks SMS): __
Best quotes (exact words):
  1. "..."
  2. "..."
Surprises (things I didn't expect):
H1 __ H2 __ H3 __ H4 __ H5 __   (✔ supports / ✘ against / – no info)
```

## 5. Timeline sheet (fill in during section C)

| SIP month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Paid? (✔ / ✘ / skipped / paused) | | | | | | | | | | | | |
| Something happened? | | | | | | | | | | | | |
| How they felt (😀😐😟) | | | | | | | | | | | | |

---

## 6. Synthesis (fill in after all interviews → Evidence Log §7)

**Per hypothesis:**

| Hypothesis | P1 | P2 | P3 | P4 | P5 | P6 | Verdict |
|---|---|---|---|---|---|---|---|
| H1 system failure → distrust | | | | | | | |
| H2 silent, self-blamed balance failures | | | | | | | |
| H3 found out late | | | | | | | |
| H4 failure → unclear recovery → stop | | | | | | | |
| H5 continuers have a buffer/habit | | | | | | | |

**AI finding vs research:**

| AI finding | Confirmed / Nuanced / Contradicted / New | Evidence (P#, quote) |
|---|---|---|
| Payment failures cluster in months 2–6 | | |
| Mostly system-side, not low balance | | |
| Bad payment experience → distrust → switch app | | |
| Support doesn't resolve it | | |
| Markets are a minor reason | | |
| People want pause/skip/modify instead of cancel | | |
| *(New things the AI missed)* | New | |

**What separates continuers from stoppers?** *(one paragraph)*
**What the interviews changed** compared with the AI findings *(this feeds the Step 8 evolution story; it's graded)*
