# RFP Intelligence Platform — Source Code & Technical Documentation

This directory contains the complete source code, tests, and runtime configuration for the **RFP Intelligence Platform** (Emplay AI Engineering Assignment).

---

## 1. Directory Structure

```
source_code/
├── main.py                  # CLI runner and entrypoint script
├── pyproject.toml           # Packaging, dependencies, and pytest configuration
├── .env.example             # Template for API keys and environment variables
├── src/
│   └── rfp_intelligence/
│       ├── __init__.py
│       ├── config.py        # Pydantic BaseSettings configuration
│       ├── cli.py           # Typer CLI application (extract, ask, serve)
│       ├── models/
│       │   ├── __init__.py
│       │   └── domain.py    # Pydantic schemas (20 fields, citations, chunks)
│       ├── ingestion/
│       │   ├── __init__.py
│       │   └── parser.py    # Document parsers (HTML/PDF) & bid folder discovery
│       ├── search/
│       │   ├── __init__.py
│       │   └── engine.py    # Hybrid search engine (Chroma + BM25Okapi + RRF)
│       ├── agents/
│       │   ├── __init__.py
│       │   └── state.py     # LangGraph AgentState TypedDict
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py       # FastAPI REST endpoints (/health, /index, /search, /ask)
│       └── utils/
│           ├── __init__.py
│           └── logging.py   # Structured logging utility
├── tests/
│   ├── test_config.py       # Configuration defaults tests
│   └── test_models.py       # Schema validation and JSON export tests
├── data/
│   ├── bids/                # Container for local bid documents
│   └── processed/           # Persistent Chroma vector store
└── eval/                    # Retrieval evaluation datasets & scripts
```

---

## 2. Setup & Installation

```bash
# 1. From repository root or source_code folder:
pip install -e deliverables/source_code

# 2. Configure environment:
cp deliverables/source_code/.env.example deliverables/source_code/.env
# Set GEMINI_API_KEY in .env

# 3. Run unit tests:
pytest deliverables/source_code/tests
```

---

## 3. Running the System

```bash
# Direct extraction on any bid package:
python deliverables/source_code/main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"

# Grounded natural-language Q&A:
python deliverables/source_code/main.py ask "What is the submission deadline for Bid1 after all addendums?"

# Launch REST API:
python deliverables/source_code/main.py serve --host 127.0.0.1 --port 8000
```

---

## 4. Key Architectural Decisions

- **LLM Provider**: `gemini/gemini-2.0-flash` routed via LiteLLM for high throughput, massive context window, and fast structured output extraction.
- **Embeddings**: `gemini/text-embedding-004` routed via LiteLLM for zero native ML compilation overhead on Windows Python 3.13.
- **Vector Store**: Chroma local directory persistence.
- **Lexical Search**: `rank_bm25` (BM25Okapi) for exact part/bid numbers.
- **Hybrid Fusion**: Reciprocal Rank Fusion (RRF) with metadata filtering.
- **Agent Orchestrator**: LangGraph StateGraph with shared state and validation feedback loops.
