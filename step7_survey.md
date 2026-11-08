# Step 7b: Quick survey (puts numbers on what the interviews find)

**Goal:** 25+ responses by **Sun 12 PM**, from first-time SIP investors. ~2 minutes, anonymous.
**Why:** interviews tell you *why*, and the survey tells you *how many*. For example: "X% didn't know their instalment had failed". That supports the problem statement and the Data & Metrics score.
**Send it to:** the same groups as your recruitment message, plus your interviewees (ask them to forward it).

---

## Build it in Google Forms (forms.google.com → Blank form)

**Form title:** First SIP: 2-minute survey
**Description (paste):**
> For a student product-research project about first SIPs. Anonymous: no name, phone, PAN, account details or amounts are asked. Takes 2 minutes. Not investment advice.

**Settings:** ⚙ Settings → Responses → **"Collect email addresses: Do not collect"**. Leave "Limit to 1 response" **off**, so people don't need to sign in.

### Section 1: About you

**1. Which app is your SIP on?** *(Multiple choice, required)*
Groww · Zerodha (Coin) · INDmoney · Paytm Money · Other · I don't have a SIP

**2. When did you start your first-ever SIP?** *(Multiple choice, required)*
Less than 3 months ago · 3–6 months ago · 6–12 months ago · 12–15 months ago · More than 15 months ago

**3. What best describes your income?** *(Multiple choice, required)*
Student (stipend / pocket money) · Salaried, first job · Salaried, 2+ years · Freelance / gig · Business · Other

**4. Has a SIP instalment ever failed, bounced or not gone through?** *(Multiple choice, required)*
- Yes, and I knew at the time
- Yes, but I found out later
- Not sure
- No, never

➜ **Skip logic:** click ⋮ on this question → **"Go to section based on answer"**:
- "Yes, and I knew at the time" → Section 2
- "Yes, but I found out later" → Section 2
- "Not sure" → Section 3
- "No, never" → Section 3

### Section 2: About the failed instalment
*(Add section: the "=" icon in the right toolbar)*

**5. How did you find out?** *(Multiple choice)*
App notification · SMS / email from my bank · Bank statement · Noticed it in my portfolio later · Someone told me · Don't remember

**6. What happened next?** *(Checkboxes: pick all that apply)*
It went through by itself next month · I retried / paid manually · I changed the SIP date or amount · I skipped or paused the SIP · I stopped the SIP · I contacted support · Not sure

### Section 3: Timing and ideas

**7. When does your money usually arrive, compared with your SIP date?** *(Multiple choice, required)*
- My SIP date is **before** my money arrives
- My SIP date is **0–2 days after** my money arrives
- My SIP date is **3+ days after** my money arrives
- My income date **changes** month to month
- I don't know my SIP date

**8. Which of these would help you most?** *(Multiple choice, required)*
- A: The app suggests a SIP date just after my money arrives
- B: If a payment fails, one clear message: what happened, what happens next, and a one-tap fix
- C: When I want to stop, an easy option to skip just one month (stopping stays just as easy)
- None of these
- Other… *(turn on "Other")*

**9. Anything else about your SIP payments?** *(Paragraph, optional)*

**10. Consent** *(Checkbox, required)*
"I understand my answers are anonymous and may be summarised in a student project."

➜ **Send** → link icon → **Shorten URL** → copy the link into your messages.

---

## WhatsApp message to send with it
> Hi all! 2-minute anonymous survey for my product research project on **first SIPs** 🙏 No personal or financial details asked. If you've ever started a SIP, please fill it and forward: [LINK]

---

## What we'll compute from it (send me the CSV: Responses → ⋮ → Download)
- **% whose instalment ever failed** (Q4), and **% of those who found out later** (Q4/Q5). These test H1/H3.
- **% whose SIP date falls before their money arrives** (Q7). This tests H2, the timing/cash-flow failures.
- **What happened after a failure** (Q6): how often a failure led to a stop or skip. This tests H4.
- **Concept preference** (Q8), compared with the interview picks.
- Splits by income type (Q3), e.g. students vs salaried.

**Be honest about the limits in the deck:** it's a convenience sample from your own network, small and not representative. Report counts ("9 of 27") next to percentages.
