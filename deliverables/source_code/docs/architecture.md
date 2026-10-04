# System Architecture & Technical Specification

This document details the engineering architecture of the **RFP Intelligence Platform**, directly implementing the pipeline specified in the Emplay AI assignment.

**Live Cloud Deployment:** [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)  

---

## 1. System Communication & Flow Diagram

```mermaid
flowchart TD
    classDef storage fill:#f9f0ff,stroke:#6b21a8,stroke-width:2px;
    classDef agent fill:#e0f2fe,stroke:#0369a1,stroke-width:2px;
    classDef parser fill:#fef3c7,stroke:#b45309,stroke-width:2px;
    classDef output fill:#ecfdf5,stroke:#047857,stroke-width:2px;

    subgraph INGESTION["1. Ingestion & Document Preprocessing"]
        Docs["Raw Documents: HTML & Multi-page PDFs"]:::parser --> Detect["Format Detector & Text Cleaner: PyMuPDF & BeautifulSoup"]:::parser
        Detect --> Chunker["Table & Section Aware Chunker: Hierarchical Metadata Tagging"]:::parser
    end

    subgraph INDEX["2. Dual-Indexed Hybrid Storage"]
        Chunker --> Embed["Dense Vector Embeddings: ChromaDB Persistent Store"]:::storage
        Chunker --> BM25Index["BM25 Lexical Keyword Index: Token Statistics & Inverted Index"]:::storage
        Embed --> ChromaDB[("Chroma Vector Store: Local Persistent Collection")]:::storage
    end

    subgraph SEARCH["3. Hybrid RAG Search Engine"]
        ChromaDB & BM25Index --> SearchTool["Hybrid Search Engine: Dense + BM25 Reciprocal Rank Fusion RRF k=60"]:::storage
    end

    subgraph AGENTS["4. Multi-Agent Orchestration (LangGraph)"]
        UserGoal["User Goal / Extraction Goal / User Question"] --> Orchestrator["Orchestrator & Planner Agent: Task Decomposition & Routing"]:::agent
        
        Orchestrator --> RetrievalAgent["Retrieval Agent: Query Understanding, Rewriting & Metadata Filter"]:::agent
        RetrievalAgent <-->|Calls Tool with Queries| SearchTool
        SearchTool -->|Ranked Evidence + Citations| RetrievalAgent
        
        RetrievalAgent --> ExtractionAgents["Specialist Extraction Agents: Dates, Legal, Product Specs"]:::agent
        ExtractionAgents --> AddendumReconciler["Addendum Reconciliation Agent: Resolves Superseding Amendments"]:::agent
        
        AddendumReconciler --> Validator["Validator & Critic Agent: Provenance, Format & Hallucination Guard"]:::agent
        
        Validator -- "Rejection / Inconsistency (Max 2 retries)" --> Orchestrator
        Validator -- "Passed Verification" --> ReportAgent["Q&A & Report Agent: Synthesizes Final Output"]:::agent
    end

    subgraph OUTPUTS["5. Deliverables"]
        ReportAgent --> JSONOut["Structured Bid Record: 20 Fields + Citations + Confidence"]:::output
        ReportAgent --> QAOut["Cited Response: File & Page Provenance"]:::output
    end
```

---

## 2. Component Responsibilities

1. **Ingestion & Parsing (`rfp_intelligence.ingestion`)**:
   - Parses HTML portal pages and multi-page PDFs using PyMuPDF and BeautifulSoup.
   - Extracts tables and normalizes whitespace, headers, and footers.
   - Attaches provenance metadata (`bid_id`, `file_name`, `doc_type`, `addendum_number`, `page_number`, `hierarchy_level`).

2. **Dual-Indexed Hybrid Search Engine (`rfp_intelligence.search`)**:
   - Indexes text chunks into Chroma (dense vectors) and BM25 (sparse keyword index).
   - Merges results via Reciprocal Rank Fusion ($k=60$) and applies metadata filtering.
   - Provides exact file provenance and page number citations.
   - Performs balanced cross-bid partitioning for comparative queries.

3. **Multi-Agent Orchestrator (`rfp_intelligence.agents`)**:
   - Managed with LangGraph StateGraph holding shared `AgentState`.
   - **Orchestrator**: Decomposes user goal into subtasks and handles retry routing.
   - **Retrieval Agent**: Formulates queries, calls hybrid search, filters results.
   - **Specialist Extraction Agents**: Extract target fields strictly from evidence without speculation.
   - **Addendum Reconciliation Agent**: Resolves base RFP terms against addenda via chronological hierarchy.
   - **Validator / Critic Agent**: Ensures every value is grounded, correctly formatted, and verified against citations before approval.
   - **Q&A / Report Agent**: Synthesizes natural-language answers backed by source citations.

4. **Strategic Decision & Qualification Agents**:
   - **BidComparisonAgent (`comparison.py`)**: Renders side-by-side matrices across multiple bids.
   - **GoNoGoAgent (`gonogo.py`)**: Evaluates bid requirements against corporate capabilities profile and emits strategic qualification scores.
