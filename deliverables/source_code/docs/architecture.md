# Architecture Specification

This document illustrates the high-level architecture of the **RFP Intelligence Platform**, directly implementing the pipeline specified in the assignment.

## Pipeline Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion & Parsing"]
        A[HTML / PDF Files] --> B[HTML & PDF Parsers<br/>BeautifulSoup / PyMuPDF]
        B --> C[Clean Text, Tables & Metadata<br/>bid_id, doc_type, addendum_no, page]
    end

    subgraph Indexing["2. Chunking & Indexing"]
        C --> D[Chunking Strategy<br/>Section & Table Aware]
        D --> E[Gemini Embeddings<br/>text-embedding-004]
        D --> F[Keyword Lexical Index<br/>BM25]
        E --> G[(Vector Store<br/>Chroma)]
    end

    subgraph Search["3. Hybrid Search Engine"]
        G & F --> H[Hybrid Search Engine<br/>Dense + BM25 with RRF & Filters]
        H --> I[Search Tool Interface<br/>REST API & Python Tool]
    end

    subgraph MultiAgent["4. Multi-Agent System (LangGraph)"]
        J[User Request / Bid Extraction Goal] --> K[Orchestrator / Planner Agent]
        K --> L[Retrieval Agent<br/>Query Rewrite & Tool Call]
        L <--> I
        L --> M[Extraction Specialist Agents<br/>Dates, Legal, Specs]
        M --> N[Addendum Reconciliation Agent<br/>Detects & Applies Overrides]
        N --> O[Validator / Critic Agent<br/>Evidence & Consistency Verification]
        O -- "Retry on Failure<br/>(Max 2 retries)" --> K
    end

    subgraph Outputs["5. Deliverables"]
        O --> P[Structured JSON Output<br/>20 Fields + Citations + Confidence]
        O --> Q[Q&A Grounded Cited Answers]
    end
```

## Component Responsibilities

1. **Ingestion & Parsing (`rfp_intelligence.ingestion`)**:
   - Parses HTML portal pages and multi-page PDFs.
   - Extracts tables and normalizes whitespace, headers, and footers.
   - Attaches provenance metadata (`bid_id`, `file_name`, `doc_type`, `addendum_number`, `page_number`).

2. **Hybrid Search Engine (`rfp_intelligence.search`)**:
   - Indexes text chunks into Chroma (dense vectors) and BM25 (sparse keyword index).
   - Merges results via Reciprocal Rank Fusion (RRF) and supports metadata filtering.
   - Provides citations with file provenance and page numbers.

3. **Multi-Agent Orchestrator (`rfp_intelligence.agents`)**:
   - Managed with LangGraph StateGraph holding shared `AgentState`.
   - **Orchestrator**: Decomposes user goal into subtasks.
   - **Retrieval Agent**: Formulates queries, calls hybrid search, filters results.
   - **Extraction Agents**: Populate target fields strictly from evidence.
   - **Addendum Reconciliation Agent**: Resolves base RFP terms against addendums.
   - **Validator / Critic Agent**: Ensures every value is grounded, correctly formatted, and verified against citations before approval.
   - **Q&A / Report Agent**: Synthesizes natural-language answers backed by source citations.
