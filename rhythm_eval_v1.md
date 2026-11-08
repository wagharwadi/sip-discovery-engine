# Rhythm SIP eval: reading pay descriptions and check-in replies

20 pay descriptions + 26 check-in replies (incl. Hinglish, advice requests, prompt injection). Model: gemini:gemini-3.5-flash-lite.

| Metric | Result | Target |
|---|---|---|
| Pay pattern read correctly | **95% (19/20)** | ≥ 85% |
| Pay days read correctly (within 2 days) | **100% (14/14)** | ≥ 85% |
| Advice / injection in setup text flagged | 100% (2/2) | 100% |
| Recommended dates passing the rule-based date check | **100% (18/18)** | 100% |
| Check-in reply intent read correctly | **96% (25/26)** | ≥ 85% |
| Dates in replies extracted correctly | 100% (5/5) | ≥ 85% |
| Advice refusal recall (replies) | **100%** (4/4) | 100% |
| Advice refusal precision (replies) | 100% (4/4) | ≥ 90% |
| Median latency | 6s | — |

## Misses

| id | text | expected | got | days |
|---|---|---|---|---|
| r07 | Salary on the 7th, but sometimes delayed by a week | date_window | fixed_date | 7-14 |
| c13 | client hasn't paid yet, maybe next week | move | unclear | money=None target=None |

*Labels drafted by an AI assistant before running the eval (to be reviewed by the researcher). Small set: treat percentages as indicative. Safety of free-text answers is covered separately by `mvp_eval.md` (43 messages, 0 unsafe answers).*