# RFP Intelligence Platform

> **AI Engineering Assignment — Emplay Inc**  
> Autonomous Hybrid RAG Search Engine & Multi-Agent System for Request for Proposal (RFP) Ingestion, Extraction, and Strategic Decision Support.

[![Live Web Application](https://img.shields.io/badge/Live%20App-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://priyanshu-emplayai.streamlit.app)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/Tests-16%2F16%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](deliverables/source_code/tests/)

---

## 🚀 Live Cloud Deployment

Experience the complete running platform with zero local setup:

> 🌐 **Public Live Platform:** [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)  
> *Pre-configured with an active evaluation model (`groq/openai/gpt-oss-120b`), streaming tokens, real-time query decomposition traces, full 20-field structured extractions, side-by-side bid comparisons, and quantitative retrieval benchmarks.*

---

## 📦 Deliverables Hub

All required submission artifacts specified in Section 11 of the assignment specification are organized within the [**`deliverables/`**](deliverables/) directory:

| Deliverable | Description | Path |
|---|---|---|
| **1. Source Code** | Complete Python codebase (ingestion, hybrid search, LangGraph agents, API/CLI, tests) | [`deliverables/source_code/`](deliverables/source_code/) |
| **2. Technical Documentation** | Setup instructions, dependencies, execution modes, chunking, and architectural decisions | [`deliverables/source_code/README.md`](deliverables/source_code/README.md) |
| **3. Architecture Diagram** | Visual Mermaid diagrams showing search engine, agent roles, and communication flows | [`deliverables/architecture_diagram.md`](deliverables/architecture_diagram.md) |
| **4. JSON Output Files** | Structured extraction records (20 fields + citations + confidence) for Bid1 & Bid2 | [`deliverables/outputs/`](deliverables/outputs/) |
| **5. Retrieval Evaluation Report** | 16-query benchmark measuring Recall@3, Recall@5, and MRR across 4 retrieval strategies | [`deliverables/retrieval_evaluation_report.md`](deliverables/retrieval_evaluation_report.md) |
| **6. Sample Q&A Log** | 10 representative natural-language questions with verified cited answers and overrides | [`deliverables/sample_qa_log.md`](deliverables/sample_qa_log.md) |
| **7. Agent Execution Trace** | Step-by-step trace log of agent inputs, tool invocations, tokens, latencies, and validation | [`deliverables/agent_trace.md`](deliverables/agent_trace.md) |
| **8. Bid Comparison Report (Bonus)** | Side-by-side comparative analysis matrix of Bid1 and Bid2 | [`deliverables/bid_comparison_report.md`](deliverables/bid_comparison_report.md) |
| **9. Live Hosted App & Walkthrough** | Public live deployment link ([`priyanshu-emplayai.streamlit.app`](https://priyanshu-emplayai.streamlit.app)) and evaluation guide | [`deliverables/demo.md`](deliverables/demo.md) |

---

## 💻 Local Setup & Execution Modes

In accordance with Section 9 of the assignment (*"The system must be runnable with one command after setup"*):

### Option A: One-Click Launch Script

- **macOS / Linux:**
  ```bash
  cd deliverables/source_code
  bash run.sh
  ```

- **Windows (PowerShell):**
  ```powershell
  cd deliverables/source_code
  powershell -ExecutionPolicy Bypass -File .\run.ps1
  ```

*The script creates a virtual environment, installs dependencies, verifies pre-computed indices, launches the FastAPI backend (port 8000) and Streamlit Web UI (port 8501), and opens your browser.*

---

### Option B: Interactive CLI & Service Commands

```bash
# 1. Install dependencies
pip install -e deliverables/source_code
pip install streamlit

# 2. Run unit tests (all 16 passing)
pytest deliverables/source_code/tests -v

# 3. Run retrieval evaluation benchmark
python deliverables/source_code/eval/evaluate_retrieval.py

# 4. Streamlit Web UI
streamlit run deliverables/source_code/web_ui.py

# 5. Interactive REST API (FastAPI / Swagger UI at http://127.0.0.1:8000/docs)
python deliverables/source_code/main.py serve --port 8000

# 6. Extract 20 fields from any bid directory
python deliverables/source_code/main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"

# 7. Ask grounded questions with exact page citations
python deliverables/source_code/main.py ask "What is the submission deadline for Bid1 after all addendums?" --bid Bid1

# 8. Side-by-side comparative analysis of extracted bids
python deliverables/source_code/main.py compare deliverables/outputs/Bid1.json deliverables/outputs/Bid2.json

# 9. Automated Go / No-Go bid qualification
python deliverables/source_code/main.py gonogo --bid deliverables/outputs/Bid1.json

# 10. Run with Docker Compose
cd deliverables/source_code && docker compose up --build
```

---

## 📊 Assignment Data

The provided input files are located in [**`Assignment-Data-Statements (AI Engineer-Emplay Inc)/`**](Assignment-Data-Statements%20(AI%20Engineer-Emplay%20Inc)/):
- `Assignment-AI Engineer.pdf`: The official assignment specification.
- `Bid1/`: Student & Staff Computing Devices (HTML bid portal page, RFP PDF, Addendum 1 PDF, Addendum 2 PDF).
- `Bid2/`: Dell Laptops w/ Extended Warranty (HTML bid portal page, PORFP PDF, Specs PDF, Contract Affidavit, Mercury Affidavit).

*The platform accepts any unseen bid folder with a similar structure passed via the `--bid` parameter.*
