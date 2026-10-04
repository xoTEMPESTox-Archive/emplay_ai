# Assignment Deliverables Hub

Welcome to the deliverables repository for the **RFP Intelligence Platform** (Emplay AI Engineering Assignment).

This directory aggregates all primary submission artifacts required by Section 11 of the assignment specification.

---

## Deliverables Summary Matrix

| # | Deliverable | Description | File / Location | Status |
|---|---|---|---|---|
| **1** | **Source Code** | Full Git repository containing ingestion pipeline, hybrid RAG search engine, multi-agent orchestration, CLI, and REST API | [`source_code/`](source_code/) & [`source_code/main.py`](source_code/main.py) | 🟢 Scaffolded & Verified |
| **2** | **Technical Documentation** | Setup instructions, dependencies, execution modes, chunking, embeddings, retrieval strategy, agent framework, prompts | [`README.md`](../README.md) | 🟢 Complete |
| **3** | **Architecture Diagram** | Comprehensive diagram showing the search engine, agents, and their communication flow | [`architecture_diagram.md`](architecture_diagram.md) | 🟢 Complete |
| **4** | **JSON Output Files** | Structured extraction records (20 fields + source citations + confidence + addendum log) for Bid1 and Bid2 | [`outputs/Bid1.json`](outputs/Bid1.json)<br/>[`outputs/Bid2.json`](outputs/Bid2.json) | 🟡 Stubs / Schemas Ready (Run in Phase 4) |
| **5** | **Retrieval Evaluation Report** | 15+ test questions, ground-truth passages, Recall@k and MRR comparative benchmark table | [`retrieval_evaluation_report.md`](retrieval_evaluation_report.md) | 🟡 Structure Ready (Evaluated in Phase 5) |
| **6** | **Sample Q&A Log** | 10+ representative queries across bids with cited answers and addendum reasoning | [`sample_qa_log.md`](sample_qa_log.md) | 🟡 Curated Questions (Run in Phase 3/6) |
| **7** | **Agent Execution Trace** | Full step-by-step observability log of agent actions, tool calls, and outputs | [`agent_trace.md`](agent_trace.md) | 🟡 Template Ready (Run in Phase 3/6) |
| **8** | **Demo Video / Live Demo** | 5–10 minute recorded walkthrough and instructions for interactive evaluation | [`demo.md`](demo.md) | 🟡 Link & Checklist Ready |

---

## Quick Navigation

- **View Architecture Diagram**: [architecture_diagram.md](architecture_diagram.md)
- **Inspect JSON Outputs**: [outputs/](outputs/)
- **Review Evaluation Framework**: [retrieval_evaluation_report.md](retrieval_evaluation_report.md)
- **Review Sample Q&A Log**: [sample_qa_log.md](sample_qa_log.md)
- **Inspect Agent Execution Trace**: [agent_trace.md](agent_trace.md)
- **Watch Demo Video / Live Demo Guide**: [demo.md](demo.md)
