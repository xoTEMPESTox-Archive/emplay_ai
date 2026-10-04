# Assignment Deliverables Hub

Welcome to the deliverables repository for the **RFP Intelligence Platform** (Emplay AI Engineering Assignment).

> 🚀 **Public Live Application:** [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)  
> *Fully interactive live cloud deployment featuring Q&A with real-time traces, 20-field extractions, side-by-side bid comparisons, and quantitative retrieval evaluation.*

This directory aggregates all primary submission artifacts required by Section 11 of the assignment specification, along with completed bonus deliverables.

---

## Deliverables Summary Matrix

| # | Deliverable | Description | File / Location | Status |
|---|---|---|---|---|
| **1** | **Source Code** | Ingestion pipeline, hybrid RAG search engine (Chroma + BM25Okapi + RRF), multi-agent LangGraph system, CLI, and FastAPI backend | [`source_code/`](source_code/) | 🟢 Complete & Verified |
| **2** | **Technical Documentation** | Setup instructions, dependencies, execution modes, chunking, embeddings, retrieval strategy, agent framework, prompts | [`README.md`](../README.md) & [`source_code/README.md`](source_code/README.md) | 🟢 Complete |
| **3** | **Architecture Diagram** | Comprehensive Mermaid diagram showing the hybrid search engine, multi-agent communications, and state transitions | [`architecture_diagram.md`](architecture_diagram.md) | 🟢 Complete |
| **4** | **JSON Output Files** | Extracted records (20 fields + source citations + confidence + addendum reconciliation) for Bid1 and Bid2 | [`outputs/Bid1.json`](outputs/Bid1.json)<br/>[`outputs/Bid2.json`](outputs/Bid2.json) | 🟢 Complete & Verified |
| **5** | **Retrieval Evaluation Report** | 16 test questions, ground-truth passages, Recall@3, Recall@5, and MRR benchmark table | [`retrieval_evaluation_report.md`](retrieval_evaluation_report.md) | 🟢 Complete & Benchmark Ran |
| **6** | **Sample Q&A Log** | 10 representative queries across bids with cited answers, page numbers, and addendum overrides | [`sample_qa_log.md`](sample_qa_log.md) | 🟢 Complete |
| **7** | **Agent Execution Trace** | Observability log of agent DAG decomposition, tool calls, addendum conflict resolution, validation, tokens, and latency | [`agent_trace.md`](agent_trace.md) | 🟢 Complete |
| **8** | **Bid Comparison Report (Bonus)** | Side-by-side comparative analysis matrix of Bid1 and Bid2 | [`bid_comparison_report.md`](bid_comparison_report.md) | 🟢 Complete |
| **9** | **Go / No-Go Agent (Bonus)** | Automated bid qualification against configurable company capabilities (`company_capabilities.json`) | [`source_code/src/rfp_intelligence/agents/gonogo.py`](source_code/src/rfp_intelligence/agents/gonogo.py) | 🟢 Complete |
| **10** | **Semantic Cache & Metrics (Bonus)** | SQLite query/embedding caching and token/latency/cost tracking per step | [`source_code/src/rfp_intelligence/utils/semantic_cache.py`](source_code/src/rfp_intelligence/utils/semantic_cache.py) | 🟢 Complete |
| **11** | **Docker & CI Pipeline (Bonus)** | Dockerfile, Docker Compose (FastAPI + Streamlit), and GitHub Actions CI workflow | [`source_code/Dockerfile`](source_code/Dockerfile)<br/>[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | 🟢 Complete |
| **12** | **Streamlit Web UI (Bonus)** | 5-tab web dashboard with streaming tokens, decomposition steps, and expandable citations | [`source_code/web_ui.py`](source_code/web_ui.py) | 🟢 Complete |
| **13** | **Live Hosted App & Walkthrough** | Public live deployment ([`priyanshu-emplayai.streamlit.app`](https://priyanshu-emplayai.streamlit.app)), evaluation instructions, and CLI/API guide | [`demo.md`](demo.md) | 🟢 Complete & Live |

---

## Quick Navigation

- **Live Cloud Deployment**: [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)
- **View Architecture Diagram**: [architecture_diagram.md](architecture_diagram.md)
- **Inspect JSON Outputs**: [outputs/](outputs/)
  - [Bid1.json](outputs/Bid1.json)
  - [Bid2.json](outputs/Bid2.json)
- **Review Evaluation Framework**: [retrieval_evaluation_report.md](retrieval_evaluation_report.md)
- **Review Sample Q&A Log**: [sample_qa_log.md](sample_qa_log.md)
- **Inspect Agent Execution Trace**: [agent_trace.md](agent_trace.md)
- **Review Bid Comparison Report**: [bid_comparison_report.md](bid_comparison_report.md)
- **Explore Source Code**: [source_code/](source_code/)
