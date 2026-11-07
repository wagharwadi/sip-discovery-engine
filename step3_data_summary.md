# Step 3: Data collected (copy into the AI Evidence Log)

Collected 6 Nov 2026. Output: `data/filtered_data.csv` (**2,237 SIP-relevant items**). Raw files in `data/raw/` (not committed).

| Source | Raw | After dedupe | After length filter (≥30 chars, ≥6 words) | SIP-relevant (final) | Date range |
|---|---|---|---|---|---|
| Play Store (Groww, newest + most relevant) | 9,796 | 6,921 | 5,687 | **743** | 2018 – Nov 2026 |
| App Store (Groww, India, RSS max) | 500 | 393 | 208 | **28** | Sep – Nov 2026 |
| TradingQ&A (200 SIP threads) | 1,745 | 1,722 | 1,618 | **974** | 2017 – Oct 2026 |
| YouTube (15 SIP videos, Hindi + English) | 1,568 | 1,249 | 846 | **492** | 2019 – Nov 2026 |
| Reddit | 0 | – | – | **0** | – |
| **Total** | **13,609** | **10,285** | **8,359** | **2,237** | |

**Cleaning steps:** exact-text dedupe → PII removal (URLs, emails/UPI IDs, phone numbers, PAN, 9–18 digit numbers, @/u/ usernames, forum quote blocks; author names never saved) → length filter → SIP keyword filter (English + Hindi/Hinglish; for forum/YouTube comments, the thread title counts as context).

**Limitations:**
- **Reddit:** blocked (HTTP 403) for requests without API keys. Skipped. Can be added later if Reddit approves a script app.
- **App Store:** Apple's feed only returns the latest ~500 reviews, so the volume is small.
- **TradingQ&A** is a Zerodha community forum, so it mostly reflects non-Groww and more experienced users. Weight it accordingly.
- The keyword filter is broad on purpose. Step 5's LLM relevance check removes remaining off-topic items (e.g. general "mutual fund app is good" reviews).
