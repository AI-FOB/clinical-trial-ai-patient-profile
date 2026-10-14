# Clinical Trial AI Patient Profile

An interactive clinical data review platform. It ingests CDISC SDTM data into a relational SQLite database and serves a Streamlit dashboard for medical reviewers. The dashboard shows a patient's timeline (adverse events against study-drug exposure), domain-level deep-dive tabs, and an LLM-powered Text-to-SQL agent that answers natural-language questions across the whole trial database.

## Features

- **Turnkey data:** synthetic SDTM datasets (DM, AE, CM, MH, LB, EX) from the PHUSE Test Data Factory, plus a pre-built SQLite database, are committed to the repo. Clone it and run.
- **Reproducible pipeline:** scripts to re-download the source `.xpt` files and rebuild the database from scratch.
- **Reviewer dashboard:** a Streamlit + Plotly UI with a top control bar (arm / subject / theme), demographic KPI cards, an AE-vs-EX Gantt timeline, and tabs for AE, Labs, Con-Meds and Medical History.
- **Medical Reviewer AI Agent:** LangChain Text-to-SQL agent powered exclusively by **NVIDIA Nemotron-3 Super 120B** (`nvidia/nemotron-3-super-120b-a12b`) via NVIDIA NIM / AI Endpoints.

## Part of a Clinical AI Suite

This project pairs with **[clinical-r-code-compliance-agent](https://github.com/AI-FOB/clinical-r-code-compliance-agent)**. Together they cover two complementary steps of clinical trial quality assurance:

| Project | Focus | Who uses it |
|---|---|---|
| `clinical-r-code-compliance-agent` | Reviews R/statistical programming code for compliance with SOPs, CDISC and regulatory standards | Statistical programmers, QC |
| `clinical-trial-ai-patient-profile` (this repo) | Reviews the subject-level clinical *data* with visual profiles and an AI query agent | Medical monitors, data reviewers |

The compliance agent checks *how* the analysis is produced. The patient profile checks *what* the data says. Used together, they support both programming and data review.

## Project Structure

```
clinical-trial-ai-patient-profile/
|-- README.md
|-- LICENSE
|-- requirements.txt
|-- .env.example             # Template for API keys (copy to .env)
|-- .streamlit/
|   \-- config.toml
|-- app/
|   \-- main_dashboard.py    # Streamlit dashboard
|-- data/
|   |-- raw/                 # SDTM CSVs (committed)
|   \-- processed/
|       \-- clinical_data.db # SQLite database (committed)
|-- src/
|   |-- agent/
|   |   |-- llm_config.py        # NVIDIA NIM LLM client
|   |   \-- text_to_sql_agent.py # Text-to-SQL agent
|   \-- data_pipeline/
|       |-- 01_download_phuse_data.py
|       \-- 02_build_sqlite_db.py
\-- tests/
    |-- test_agent.py        # Agent smoke test (calls the live LLM)
    \-- mock_lb.py           # Generates mock LB (labs) data
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/<you>/clinical-trial-ai-patient-profile.git
cd clinical-trial-ai-patient-profile
pip install -r requirements.txt
```

### 2. Configuration

The AI agent uses the NVIDIA API only. Your key is read from a local `.env` file, which git ignores. Never commit real keys.

```bash
# macOS / Linux
cp .env.example .env
# Windows (PowerShell)
Copy-Item .env.example .env
```

Then open `.env` and set your NVIDIA API key (free at https://build.nvidia.com):

```ini
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
```

| Variable | Required | Default |
|---|---|---|
| `NVIDIA_API_KEY` | Yes (for the AI agent) | — |
| `NVIDIA_MODEL` | No | `nvidia/nemotron-3-super-120b-a12b` |

> The dashboard's visual sections work without a key. Only the AI agent needs `NVIDIA_API_KEY`.

### 3. Launch the dashboard

```bash
streamlit run app/main_dashboard.py
```

### 4. (Optional) Rebuild the data

The database is already included. To regenerate it from the PHUSE source:

```bash
python src/data_pipeline/01_download_phuse_data.py
python src/data_pipeline/02_build_sqlite_db.py
```

### 5. (Optional) Smoke-test the agent

```bash
python tests/test_agent.py
```

## Data Disclaimer

All data is **synthetic** (PHUSE Test Data Factory) and contains no real patient information.

## License

[MIT](LICENSE) © 2026 Tzu-Chien(Bruce) Chuang
