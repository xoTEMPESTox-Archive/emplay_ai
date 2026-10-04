# Deliverable: Demo Video & Live Walkthrough

This document provides links and instructions for evaluating the **RFP Intelligence Platform** via video presentation and interactive live commands.

---

## 1. Demo Video (5–10 Minutes)

- **Video Title:** RFP Intelligence Platform Walkthrough — Emplay AI Engineer Assignment
- **Video Link:** [🎥 Watch Demonstration Video (Loom / Drive Link Placeholder)](https://loom.com/share/placeholder-rfp-intelligence-demo)
- **Duration:** ~7 minutes

### Video Agenda & Timestamps
- `0:00 - 1:00` — **Introduction & Architecture Overview**: Dual-index hybrid search (Vector + BM25) and LangGraph agent workflow.
- `1:00 - 2:30` — **Document Ingestion & Indexing**: Ingesting Bid1 and Bid2 HTML & PDF documents; table parsing and chunk metadata.
- `2:30 - 4:00` — **Single-Command Bid Extraction**: Running `python main.py --bid ./Bid1`, watching agents coordinate in real time.
- `4:00 - 5:00` — **Addendum Reconciliation & Validation**: Demonstrating how Addendum 2 overrides the initial due date, and how the Critic Agent enforces strict evidence grounding.
- `5:00 - 6:00` — **Grounded Natural-Language Q&A**: Answering complex user queries with exact source citations (file name and page number).
- `6:00 - 7:00` — **Retrieval Evaluation & Benchmarks**: Comparing dense vector vs. hybrid retrieval results.

---

## 2. Interactive Live Demo (2-Minute Quick Run)

Evaluators can run the live system directly in their local environment:

### Step 1: Environment Setup
```bash
# Clone and navigate
cd emplay_ai

# Set API key in .env
echo GEMINI_API_KEY=your_key_here > .env
```

### Step 2: Run Extraction (One Command)
```bash
# Extract Bid1
python main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1"

# Or extract Bid2
python main.py --bid "Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid2"
```

### Step 3: Run Interactive Grounded Q&A
```bash
# Ask about deadline after addendums
python main.py ask "What is the submission deadline for Bid1 after all addendums?"

# Ask about affidavits
python main.py ask "Which affidavits are required for the Dell laptop bid?" --bid-id Bid2
```

### Step 4: Launch REST API & Swagger UI
```bash
python main.py serve --host 127.0.0.1 --port 8000
```
Open interactive documentation in your browser at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
