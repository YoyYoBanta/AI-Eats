# 🍽️ AI-Powered Restaurant Recommendation System

An intelligent restaurant recommendation service inspired by Zomato that combines structured restaurant data with a Groq-hosted LLM to deliver personalized, explainable recommendations.

## Features

- **Smart Filtering** — narrows thousands of restaurants using location, budget, cuisine, and rating preferences
- **AI-Powered Ranking** — Groq LLM (Llama 3.3 70B) ranks and explains each recommendation
- **Graceful Fallback** — rule-based ranking when the LLM is unavailable
- **Explainability** — every recommendation includes an AI-generated rationale

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd restaurant-recommender
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your **Groq API key**:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

> Get your free API key at [console.groq.com/keys](https://console.groq.com/keys)

### 5. Verify configuration loads

```bash
python -c "from config.settings import settings; print('✅ Config loaded:', settings.LLM_MODEL)"
```

### 6. Run the application

```bash
# Web UI (Streamlit)
streamlit run ui/streamlit_app.py

# CLI (optional)
python -m ui.cli
```

## Project Structure

```
restaurant-recommender/
├── config/
│   ├── settings.py              # Centralized configuration (pydantic-settings)
│   └── prompts/                 # Versioned LLM prompt templates
├── data/
│   └── ingestion/
│       ├── loader.py            # Hugging Face dataset loader
│       └── preprocessor.py      # Data cleaning & normalization
├── models/
│   ├── preferences.py           # UserPreference schema
│   └── recommendation.py        # Recommendation output schema
├── repositories/
│   └── restaurant_repo.py       # Data access abstraction
├── services/
│   ├── filter_engine.py         # Hard filtering logic
│   ├── prompt_builder.py        # LLM prompt assembly
│   ├── llm_client.py            # Groq API wrapper
│   ├── response_parser.py       # Parse & validate LLM JSON
│   └── recommender.py           # Full pipeline orchestrator
├── ui/
│   ├── streamlit_app.py         # Web interface
│   └── cli.py                   # Command-line interface
├── tests/                       # Unit & integration tests
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Configuration

All settings are loaded from environment variables (or a `.env` file). See [`.env.example`](.env.example) for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_DATASET_NAME` | Hugging Face dataset ID | `ManikaSaini/zomato-restaurant-recommendation` |
| `LLM_PROVIDER` | LLM provider | `groq` |
| `LLM_MODEL` | Groq model identifier | `llama-3.3-70b-versatile` |
| `GROQ_API_KEY` | Groq API key | — |
| `MAX_CANDIDATES` | Max restaurants sent to LLM | `25` |
| `TOP_K_RESULTS` | Recommendations returned to user | `5` |
| `BUDGET_LOW_MAX` | Upper bound for low tier (INR) | `500` |
| `BUDGET_MEDIUM_MAX` | Upper bound for medium tier (INR) | `1500` |
| `LLM_TIMEOUT_SECONDS` | API call timeout | `30` |
| `ENABLE_FALLBACK_RANKER` | Use rule-based fallback on LLM failure | `true` |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Dataset | `datasets` (Hugging Face) |
| Data processing | `pandas` |
| Validation | `pydantic` |
| LLM SDK | `groq` |
| Web UI | `streamlit` |
| Config | `pydantic-settings` + `.env` |
| Testing | `pytest` |

## Documentation

- [`context.md`](../context.md) — Problem statement and system workflow
- [`architecture.md`](../architecture.md) — Technical architecture and component design
- [`implementation-plan.md`](../implementation-plan.md) — Phased implementation plan
- [`edge-cases.md`](../edge-cases.md) — Edge cases and failure modes

## License

This project is for educational and demonstration purposes.
