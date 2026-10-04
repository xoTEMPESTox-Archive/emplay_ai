# Architecture Diagram: Search Engine & Multi-Agent System

This deliverable provides the architectural visualization and communication flow for the **RFP Intelligence Platform**, detailing how documents are ingested, how the hybrid search engine indexes and retrieves information, and how the multi-agent system collaborates using LangGraph.

---

## 1. System Communication & Flow Diagram

```mermaid
flowchart TD
    classDef storage fill:#f9f0ff,stroke:#6b21a8,stroke-width:2px;
    classDef agent fill:#e0f2fe,stroke:#0369a1,stroke-width:2px;
    classDef parser fill:#fef3c7,stroke:#b45309,stroke-width:2px;
    classDef output fill:#ecfdf5,stroke:#047857,stroke-width:2px;

    subgraph INGESTION["1. Ingestion & Document Preprocessing"]
        Docs[Raw Documents<br/>HTML & Multi-page PDFs]:::parser --> Detect[Format Detector & Cleaner<br/>BeautifulSoup & PyMuPDF]:::parser
        Detect --> Chunker[Table & Section Aware Chunker<br/>Metadata Tagging]:::parser
    end

    subgraph INDEX["2. Dual-Indexed Hybrid Storage"]
        Chunker --> Embed[Gemini Embedding Model<br/>text-embedding-004]:::storage
        Chunker --> BM25Index[BM25 Lexical Keyword Index<br/>rank_bm25]:::storage
        Embed --> ChromaDB[(Chroma Vector Store<br/>Local Persistent DB)]:::storage
    end

    subgraph SEARCH["3. RAG Search Engine Tool"]
        ChromaDB & BM25Index --> SearchTool[Hybrid Search Engine<br/>Dense + BM25 Fusion (RRF)<br/>Metadata Filtering & Top-K]:::storage
    end

    subgraph AGENTS["4. Multi-Agent Orchestration (LangGraph)"]
        UserGoal[User Goal / Extraction Prompt] --> Orchestrator[Orchestrator / Planner Agent<br/>Decomposes Tasks & Routes]:::agent
        
        Orchestrator --> RetrievalAgent[Retrieval / Search Agent<br/>Query Rewrite & Filter Assembly]:::agent
        RetrievalAgent <-->|Calls Tool with Queries| SearchTool
        SearchTool -->|Ranked Evidence + Citations| RetrievalAgent
        
        RetrievalAgent --> ExtractionAgents[Extraction Specialist Agents<br/>Dates, Legal, Product Specs]:::agent
        ExtractionAgents --> AddendumReconciler[Addendum Reconciliation Agent<br/>Applies Chronological Amendments]:::agent
        
        AddendumReconciler --> Validator[Validator / Critic Agent<br/>Provenance, Type & Hallucination Check]:::agent
        
        Validator -- "Rejection / Failed Field<br/>(Max 2 retries)" --> Orchestrator
        Validator -- "Passed Verification" --> ReportAgent[Q&A / Report Agent<br/>Synthesizes Final Output]:::agent
    end

    subgraph OUTPUTS["5. Deliverables"]
        ReportAgent --> JSONOut[Structured Bid Record<br/>20 Fields + Citations + Confidence]:::output
        ReportAgent --> QAOut[Cited Answer Response<br/>File & Page Provenance]:::output
    end
```

---

## 2. Agent Roles and Interaction Specifications

| Agent | Core Responsibility | Input | Output / Handoff |
|---|---|---|---|
| **Orchestrator / Planner** | Manages execution lifecycle, determines subtasks, triggers retries on validation failure | Extraction goal or user query | Subtask schedule, dispatch commands |
| **Retrieval Agent** | Expands domain queries (e.g. deadline synonyms), enforces metadata filters, queries hybrid search | Target field questions | Ranked passages with citations |
| **Extraction Specialists** | Populates field values strictly from retrieved text without speculating | Evidence chunks with citations | Candidate values with file and page references |
| **Addendum Reconciler** | Detects version differences, supersedes initial RFP values with latest addendum amendments | Base field values + Addendum text | Chronological change log and updated fields |
| **Validator / Critic** | Verifies evidence support, confirms date/number formats, rejects ungrounded values | Candidate fields and citations | Validation report (`passed`, `failed`, `not_found`) |
| **Q&A / Report Agent** | Generates human-readable summaries and exports final audited JSON records | Verified fields and citations | Structured JSON file and cited answers |
