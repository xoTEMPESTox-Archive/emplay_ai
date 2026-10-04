# RFP Intelligence Platform — Source Code & Technical Documentation

This directory contains the complete source code, tests, and runtime configuration for the **RFP Intelligence Platform** (Emplay AI Engineering Assignment).

> 🚀 **Public Live Application:** [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)  
> *Test all capabilities live without installing any local dependencies.*

---

## 1. Quickstart — One-Click Setup & Launch

You can launch the entire stack (FastAPI backend + Streamlit Web UI) with a single command:

### macOS / Linux
```bash
cd deliverables/source_code
bash run.sh
```

### Windows (PowerShell)
```powershell
cd deliverables/source_code
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

**What the scripts do automatically:**
1. Checks for a Python virtual environment (`.venv`) and creates one if absent.
2. Activates the environment.
3. Checks if packages are installed; installs them in editable mode (`pip install -e .` + `streamlit`) if missing, or skips if already present.
4. Generates `.env` from `.env.example` if no `.env` exists.
5. Deploys the FastAPI server (Port 8000) and Streamlit Web UI (Port 8501) in background.
6. Outputs clickable direct URLs in your terminal:
   - 💬 **Streamlit Web UI:** `http://localhost:8501`
   - 📡 **REST API Health:** `http://localhost:8000/health`
   - 📖 **Swagger API Docs:** `http://localhost:8000/docs`

---

## 2. Directory Structure

```
source_code/
├── main.py                  # CLI runner and entrypoint script
├── web_ui.py                # Streamlit chat interface with streaming and citations
├── run.sh                   # One-click environment bootstrap & launcher script (Bash)
├── run.ps1                  # One-click environment bootstrap & launcher script (PowerShell)
├── requirements.txt         # Pinned requirements for Streamlit Community Cloud
├── Dockerfile               # Multi-stage Docker deployment definition
├── docker-compose.yml       # Orchestrates FastAPI backend and Streamlit Web UI
├── pyproject.toml           # Packaging, dependencies, and pytest configuration
├── .env.example             # Comprehensive configuration template for all providers
├── .streamlit/
│   ├── config.toml          # Light theme default enforcement
│   └── secrets.toml.example # Template for Streamlit Cloud secrets management
├── src/
│   └── rfp_intelligence/
│       ├── __init__.py
│       ├── config.py        # Pydantic BaseSettings configuration (LiteLLM routing)
│       ├── cli.py           # Typer CLI application (extract, ask, compare, gonogo, serve)
│       ├── models/
│       │   ├── __init__.py
│       │   └── domain.py    # Pydantic schemas (20 fields, citations, chunks)
│       ├── ingestion/
│       │   ├── __init__.py
│       │   └── parser.py    # Document parsers (HTML/PDF) & bid folder discovery
│       ├── search/
│       │   ├── __init__.py
│       │   ├── decomposition.py # Query restructuring & sub-query generator
│       │   └── engine.py        # Hybrid search engine (Chroma + BM25Okapi + RRF)
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── state.py           # LangGraph AgentState TypedDict
│       │   ├── graph.py           # LangGraph StateGraph orchestration workflow
│       │   ├── tools.py           # Retrieval and extraction tool wrappers
│       │   ├── specialists.py     # Domain extraction specialist agents
│       │   ├── reconciliation.py  # Addendum conflict reconciliation agent
│       │   ├── validator.py       # Rule-based and semantic validation agent
│       │   ├── comparison.py      # Multi-bid comparative analysis agent
│       │   └── gonogo.py          # Corporate qualification recommendation agent
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py       # FastAPI REST endpoints (/health, /index, /search, /ask)
│       └── utils/
│           ├── __init__.py
│           ├── llm.py             # Unified LLM client (Ollama, LiteLLM, fallback)
│           ├── metrics.py         # Step-by-step latency, token, and cost tracker
│           ├── semantic_cache.py  # Persistent SQLite cache for prompts & embeddings
│           └── logging.py         # Structured logging utility
├── tests/
│   ├── test_config.py       # Configuration defaults and model alias tests
│   ├── test_models.py       # Schema validation and JSON export tests
│   ├── test_ingestion.py    # Parsing, table extraction, and classification tests
│   ├── test_search.py       # Hybrid retrieval, BM25, and metadata filtering tests
│   └── test_agents.py       # Agent DAG, validation loops, and addenda overrides tests
├── data/
│   ├── company_capabilities.json # Corporate profile for Go/No-Go evaluation
│   └── processed/                # Pre-computed Chroma vector store and BM25 index
└── eval/
    └── evaluate_retrieval.py     # 16-query benchmark evaluation harness
```

---

## 3. Manual Installation & Provider Switching

```bash
# 1. Install dependencies:
pip install -e deliverables/source_code
pip install streamlit

# 2. Configure .env:
cp deliverables/source_code/.env.example deliverables/source_code/.env
```

### Supported LLM & Embedding Providers

| Provider | `LLM_MODEL` setting | Required Credentials / Setup |
|---|---|---|
| **Groq (Cloud LPU)** | `groq/openai/gpt-oss-120b` *(or `groq/llama-3.3-70b-versatile`)* | Set `GROQ_API_KEY=your_key_here` in `.env` |
| **Local Ollama** (Default) | `ollama/qwen3.5:4b` | Run `ollama run qwen3.5:4b` locally |
| **Google Gemini** | `gemini/gemini-2.5-flash` | Set `GEMINI_API_KEY=AIzaSy...` in `.env` |
| **OpenAI** | `openai/gpt-4o-mini` | Set `OPENAI_API_KEY=sk-...` in `.env` |
| **Anthropic** | `anthropic/claude-3-5-sonnet-20241022` | Set `ANTHROPIC_API_KEY=sk-ant-...` in `.env` |

> [!NOTE]
> Evaluators **do not need to re-index** when switching LLMs. All 214 chunks and embeddings are pre-computed and stored in `data/processed/chroma` and `bm25_cache.json`. Changing LLM keys only affects text generation, query restructuring, and listwise reranking.

---

## 4. Execution Modes & CLI

```bash
# 1. Run unit test suite (all 16 tests passing)
pytest deliverables/source_code/tests -v

# 2. Run retrieval evaluation benchmark
python deliverables/source_code/eval/evaluate_retrieval.py

# 3. Extract 20 RFP fields from a bid folder
python deliverables/source_code/main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"

# 4. Ask grounded questions with exact citations
python deliverables/source_code/main.py ask "What is the submission deadline for Bid1 after all addendums?" --bid Bid1

# 5. Side-by-side bid comparison
python deliverables/source_code/main.py compare deliverables/outputs/Bid1.json deliverables/outputs/Bid2.json

# 6. Go / No-Go qualification evaluation
python deliverables/source_code/main.py gonogo --bid deliverables/outputs/Bid1.json
```
