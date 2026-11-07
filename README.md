# SIP Continuation Discovery Engine (Groww, first-time investors)

An AI pipeline that analyses public conversations about SIPs in India to find why first-time investors' SIPs stop within 12 months. It ranks opportunities against the metric: *% of first-time MF investors with an active SIP 12 months after their first one.*

**Live app:** [add Streamlit link] · Student research project · not investment advice.

## Pipeline
| Step | Script | Output |
|---|---|---|
| Collect | `collect/*.py` (Play Store, App Store, YouTube, TradingQ&A; Reddit blocked) | `data/raw/` (not committed) |
| Clean + filter | `clean_filter.py` | `data/filtered_data.csv` (PII removed) |
| Tag (Gemini, Groq backup) | `step5_extract.py` using `taxonomy.py` + `llm.py` | `data/tagged*.jsonl` |
| Themes (AI proposes, human reviews) | `step5_themes.py propose / assign` | `data/themes_ai_v1.json` → `data/themes.json` |
| Quantify + score | `step5_analyze.py` | `data/opportunities.csv`, `step5_results.md` |
| Validate vs golden set | `step5_validate.py` | `data/golden_agreement.csv` |
| App dataset | `engine_data.py` | `data/engine_items.csv` |
| App | `streamlit_app.py` | public link |

## Run locally
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # add your keys
streamlit run streamlit_app.py
```
