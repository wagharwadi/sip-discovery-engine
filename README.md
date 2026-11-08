# SIP Continuation Discovery Engine (Groww, first-time investors)

An AI pipeline that analyses public conversations about SIPs in India to find why first-time investors' SIPs stop within 12 months. It ranks opportunities against the metric: *% of first-time MF investors with an active SIP 12 months after their first one.*

**Live app:** https://sip-discovery-engine.onrender.com (free hosting: the first visit after a quiet spell takes ~1 min to wake up) · Student research project · not investment advice.

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

## MVP: Rhythm SIP (`rhythm_app.py`)
A SIP that moves with your money (solution: `FINAL_SOLUTION.md`). One guided flow (`web/`): each step moves on by itself once its rule checks pass.
**Design rule:** the AI only *reads* (pay description → pattern and days; check-in reply → intent and day). Fixed rules decide and verify the date (`rhythm_core.py`), and the user confirms. Free-text questions go through the safety engine (`mvp_core.py`: advice guard, 17 official-source facts, output guard).
Evals: `rhythm_eval.py` (46 labelled pay descriptions and replies) and `mvp_eval.py` (43 safety messages). All data is simulated.

## Run locally
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # add your keys
streamlit run streamlit_app.py      # Discovery Engine
python rhythm_app.py                # MVP (http://localhost:8503)
```
