# RFP Intelligence Platform

> **AI Engineering Assignment — Emplay Inc**  
> Hybrid RAG Search Engine & Multi-Agent System for Request for Proposal (RFP) Documents.

---

## 🚀 Live Product & Demonstration

Experience the running solution directly:

- 🎥 **Live Demo Video (5–10 min walk-through):** [**deliverables/demo.md**](deliverables/demo.md)
- ⚡ **Interactive One-Command Bid Extraction:**
  ```bash
  python deliverables/source_code/main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"
  ```
- 💬 **Interactive Grounded Q&A:**
  ```bash
  python deliverables/source_code/main.py ask "What is the submission deadline for Bid1 after all addendums?"
  ```
- 🌐 **Interactive REST API (Swagger UI):** Launch with `python deliverables/source_code/main.py serve` and view at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 📦 Deliverables Hub

All required deliverables specified in Section 11 of the assignment are located inside the [**`deliverables/`**](deliverables/) directory:

| Deliverable | Description | Path |
|---|---|---|
| **1. Source Code** | Complete Python codebase (ingestion, hybrid search, agents, API/CLI, tests) | [`deliverables/source_code/`](deliverables/source_code/) |
| **2. Technical Documentation** | Setup instructions, dependencies, execution modes, and architectural decisions | [`deliverables/source_code/README.md`](deliverables/source_code/README.md) |
| **3. Architecture Diagram** | Visual Mermaid diagrams showing search engine, agent roles, and communication | [`deliverables/architecture_diagram.md`](deliverables/architecture_diagram.md) |
| **4. JSON Output Files** | Structured extraction records (20 fields + citations + confidence) for Bid1 & Bid2 | [`deliverables/outputs/`](deliverables/outputs/) |
| **5. Retrieval Evaluation Report** | 16-query benchmark measuring Recall@k and MRR across retrieval strategies | [`deliverables/retrieval_evaluation_report.md`](deliverables/retrieval_evaluation_report.md) |
| **6. Sample Q&A Log** | 10 representative natural-language questions with verified cited answers | [`deliverables/sample_qa_log.md`](deliverables/sample_qa_log.md) |
| **7. Agent Execution Trace** | Step-by-step trace log of agent inputs, tool invocations, tokens, and latencies | [`deliverables/agent_trace.md`](deliverables/agent_trace.md) |
| **8. Demo Video & Live Guide** | Video demonstration link, timestamps, and interactive evaluation guide | [`deliverables/demo.md`](deliverables/demo.md) |

---

## 📊 Assignment Data

The provided input files are located in [**`Assignment-Data-Statements (AI Engineer-Emplay Inc)/`**](Assignment-Data-Statements%20(AI%20Engineer-Emplay%20Inc)/):
- `Assignment-AI Engineer.pdf`: The official assignment specification.
- `Bid1/`: Student & Staff Computing Devices (HTML bid portal page, RFP PDF, Addendum 1 PDF, Addendum 2 PDF).
- `Bid2/`: Dell Laptops w/ Extended Warranty (HTML bid portal page, PORFP PDF, Specs PDF, Contract Affidavit, Mercury Affidavit).

*The platform accepts any unseen bid folder with a similar structure passed via the `--bid` parameter.*

---

## 🛠️ Quickstart

```bash
# 1. Install dependencies
pip install -e deliverables/source_code

# 2. Run unit tests (all 4 passing)
pytest deliverables/source_code/tests

# 3. Execute extraction on Bid1
python deliverables/source_code/main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"
```

For detailed code architecture, prompts, and design decisions, please see the [**Source Code Directory**](deliverables/source_code/) and [**Progress Checklist**](PROGRESS.md).
