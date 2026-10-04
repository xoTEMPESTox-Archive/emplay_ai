# Deliverable: Live Hosted Platform & Interactive Walkthrough

This deliverable provides access to the live cloud deployment of the **RFP Intelligence Platform**, along with instructions for live interactive verification across web UI, REST API, and CLI modes.

---

## 1. Live Cloud Deployment

- **Public Live Application:** [🚀 https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)
- **Deployment Platform:** Streamlit Community Cloud
- **Pre-configured Model:** `groq/openai/gpt-oss-120b` (Shared evaluation key pre-loaded; runs in < 3s)
- **Custom Provider Support:** Evaluators can paste their own **Google Gemini**, **OpenAI**, or **Anthropic** key directly in the sidebar settings.

---

## 2. Platform Capabilities on the Live Demo

Evaluators can explore all mandatory and bonus assignment requirements directly in the cloud application across 5 dedicated tabs:

### 💬 Tab 1: RFP Intelligence Chat & Live Traces
- **Grounded Q&A:** Ask complex questions across **Bid1** (Dallas ISD Student and Staff Computing Devices) and **Bid2** (State of Maryland Dell Laptops).
- **Exact Citations:** Every answer cites source document filenames and exact page numbers.
- **Query Decomposition Trace:** Click `🔍 Query Decomposition Steps` to inspect how natural-language queries are restructured into targeted sub-queries without meta-noise.
- **Evidence Passages:** Click `📚 Source Evidence & Passages` to inspect the exact text chunks selected by the hybrid search engine and listwise reranker.
- **Observability:** Live metrics display latency in seconds and model used per query.

### 📊 Tab 2: Structured Extractions (20 Mandatory Fields)
- Interactive viewer for [`Bid1.json`](outputs/Bid1.json) and [`Bid2.json`](outputs/Bid2.json).
- Displays validation status (Passed, Failed, Not Found), confidence scores, and source citations for each of the 20 required fields.
- Includes expandable raw JSON inspection.

### ⚖️ Tab 3: Bid Comparison & Go/No-Go Decision
- Side-by-side comparative analysis of Bid1 vs. Bid2 across hardware, warranties, bonding, delivery, and affidavits.
- Automated evaluation against company capabilities emitting a strategic Go / No-Go recommendation.

### 📈 Tab 4: Retrieval Evaluation Benchmark
- Interactive quantitative benchmark table comparing **Dense Vector** vs. **BM25 Keyword** vs. **Hybrid (RRF $k=60$)** vs. **Hybrid + Listwise Reranker**.
- Shows Recall@3, Recall@5, and Mean Reciprocal Rank (MRR) across 16 ground-truth queries.

### 🏗️ Tab 5: Multi-Agent Architecture
- Interactive Mermaid flowchart visualizing document ingestion, dual-index storage, hybrid retrieval, LangGraph agent coordination, and the validator feedback loop.

---

## 3. One-Click Local Reproduction

In accordance with Section 9 of the assignment (*"The system must be runnable with one command after setup"*), evaluators can also run the entire platform locally with a single command:

### macOS / Linux
```bash
git clone https://github.com/xoTEMPESTox-Archive/emplay_ai.git
cd emplay_ai/deliverables/source_code
bash run.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/xoTEMPESTox-Archive/emplay_ai.git
cd emplay_ai/deliverables/source_code
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

### Docker
```bash
docker compose up --build
```

The script automatically bootstraps the virtual environment, verifies dependencies, starts the FastAPI backend on port 8000, starts the Streamlit UI on port 8501, and opens the browser.

