# Deliverable: Retrieval Evaluation Report

This report documents the quantitative retrieval evaluation framework designed to benchmark search quality across **Bid1** and **Bid2**, comparing multiple retrieval configurations in accordance with Section 6.4 of the Emplay AI assignment.

**Live Application Benchmark:** Available interactively under Tab 4 at [https://priyanshu-emplayai.streamlit.app](https://priyanshu-emplayai.streamlit.app)  

---

## 1. Evaluation Methodology

The search engine is evaluated using a curated benchmark of **16 ground-truth questions** targeting diverse RFP information types (exact solicitation numbers, submission deadlines, legal affidavits, hardware specifications, addenda modifications, and commercial terms).

### Evaluation Metrics
- **Recall@3**: Proportion of queries where a relevant ground-truth chunk appears within the top 3 retrieved results.
- **Recall@5**: Proportion of queries where a relevant ground-truth chunk appears within the top 5 retrieved results.
- **MRR (Mean Reciprocal Rank)**: $\frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$, measuring the precision and ranking quality of the first relevant evidentiary chunk.

---

## 2. Benchmark Evaluation Question Set

| # | Bid | Query / Question | Target Document | Expected Evidence / Concept |
|---|---|---|---|---|
| 1 | Bid1 | What is the solicitation or bid number? | HTML / RFP Final | `ja-207652, 207652` |
| 2 | Bid1 | What was the original submission deadline? | RFP Final | `june 25, 2024, 2:00 pm, june 25, june 27` |
| 3 | Bid1 | What is the final submission due date after Addendum 2? | Addendum 2 | `july 9, 2024, addendum 2, july 9` |
| 4 | Bid1 | Is a bid bond or deposit required and how much? | RFP Final | `bid bond, 5%, security deposit, bond` |
| 5 | Bid1 | What are the mandatory device specifications for display and processor? | RFP Final | `11.6, 14, chromebook, processor, ram, intel` |
| 6 | Bid1 | Are installation white glove or deployment services required? | RFP Final | `white glove, asset tag, deployment, services, installation` |
| 7 | Bid1 | What changes were introduced specifically in Addendum 1? | Addendum 1 | `addendum 1, timeline, inquiries, clarification` |
| 8 | Bid1 | Who is the primary procurement buyer contact and email? | HTML BidNet Page | `purchasing, contact, email, phone, buyer, bidnet` |
| 9 | Bid2 | What is the bid number for the Dell laptop solicitation? | HTML / PORFP | `001it836371, bpm044439, 836371, bpm044557` |
| 10 | Bid2 | Which specific affidavits are required with the bid submission? | Contract & Mercury Affidavits | `contract affidavit, mercury affidavit, affidavit` |
| 11 | Bid2 | What processor, RAM, and SSD specs are specified for Dell laptops? | Dell_Laptop_Specs.pdf | `latitude, core i5, 16gb, 256gb, 512gb, dell` |
| 12 | Bid2 | What warranty coverage is mandated for the Dell laptops? | PORFP / Specs | `prosupport, 3 year, warranty, next business day` |
| 13 | Bid2 | What are the payment terms specified in the PORFP? | PORFP | `net 30, invoice, payment, state of maryland` |
| 14 | Bid2 | Is attendance at a pre-bid conference mandatory? | PORFP / HTML | `pre-bid, conference, none, mandatory, meeting` |
| 15 | Bid2 | What manufacturer authorization is required from Dell? | PORFP | `authorized, partner, letter, oem, reseller, dell` |
| 16 | Cross-Bid | Compare the warranty requirements between Bid1 and Bid2. | Cross-Bid Documents | `warranty, prosupport, support, guarantee` |

---

## 3. Comparative Benchmark Results

| Retrieval Strategy | Recall@3 | Recall@5 | MRR | Latency (avg) | Notes |
|---|---|---|---|---|---|
| **Dense Vector Search** (`qwen3-embedding` / Chroma) | **62.5%** | **68.8%** | **0.5958** | ~45 ms | Semantic embeddings capture conceptual intent well but struggle with exact alphanumeric bid numbers. |
| **BM25 Keyword Search** (BM25Okapi) | **75.0%** | **81.2%** | **0.7413** | ~4 ms | Excels at exact solicitation IDs (`JA-207652`, `001IT836371`), weaker on conceptual synonyms. |
| **Hybrid Search** (Dense + BM25 with RRF $k=60$) | **68.8%** | **81.2%** | **0.7266** | ~50 ms | Reciprocal Rank Fusion ($k=60$) balances exact identifiers with semantic understanding. |
| **Hybrid Search + Reranker** (RRF + Reranker) | **81.2%** | **81.2%** | **0.7292** | ~120 ms | RRF fusion combined with listwise/lexical density reranking achieves top recall across all queries. |

---

## 4. Architectural Reasoning Behind Retrieval Decisions

### A. Why Hybrid Search (Dense + BM25) Over Vector-Only RAG
Standard vector-only RAG pipelines frequently fail in enterprise RFP analysis:
1. **Sub-Word Tokenization Fracture:** Dense embedding models split alphanumeric solicitation numbers (e.g. `JA-207652`, `001IT836371`, `BPM044439`) into arbitrary sub-word tokens (`JA`, `-`, `207`, `652`), diffusing their representation in vector space. As a result, vector similarity searches for exact bid numbers yield poor precision.
2. **Inverted Index Exact Match:** BM25 tokenization treats alphanumeric identifiers as discrete keywords. When a user asks *"What is the deadline for JA-207652?"*, BM25 scores chunks containing `JA-207652` with near-infinite inverse document frequency (IDF), guaranteeing top ranking.
3. **Semantic Fallback:** Conversely, BM25 fails when users ask conceptually framed questions like *"What are the deployment and unboxing requirements?"* where the RFP text uses *"white glove services and asset tagging"*. Here, dense vector search bridges the semantic gap.

### B. Why Reciprocal Rank Fusion (RRF with $k=60$) Over Linear Score Combination
1. **Scale Incompatibility:** Dense cosine similarity produces scores bounded in $[0, 1]$, whereas BM25 produces unbounded scores $[0, \infty)$ proportional to document length and term frequency. 
2. **Brittle Normalization:** Min-Max normalization of BM25 scores degrades when corpus size changes or when outlier terms skew the distribution.
3. **RRF Robustness:** Reciprocal Rank Fusion relies purely on rank position rather than raw score magnitudes:
   $$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
   Setting $k=60$ (the canonical information retrieval standard by Cormack et al.) prevents a single extreme rank from dominating the final fused list, while rewarding documents that appear near the top in both dense and sparse retrieval passes.

### C. Balanced Cross-Bid Retrieval Partitioning
When querying across bids (e.g., *"Compare the warranty terms between Bid1 and Bid2"*), standard single-pool retrieval often returns 5 chunks from the larger document set (Bid1) and 0 chunks from the smaller set (Bid2), starving the LLM of comparative evidence.
- **Our Solution:** The Query Decomposition module identifies comparative queries, dynamically splits them into targeted sub-queries per bid (`bid_id="Bid1"` and `bid_id="Bid2"`), allocates balanced top-$k$ quotas ($top\_k/2$), and merges the results. This ensures perfectly balanced evidence representation for downstream synthesis.

### D. Chunking Strategy: Section & Table Preservation
- **Chunk Size (1,000 chars) & Overlap (150 chars):** Selected empirically to balance embedding density with context completeness. Smaller chunks (e.g. 256 chars) break tabular line items, while larger chunks (e.g. 2,048 chars) dilute semantic specificity.
- **Header & Section Propagation:** Markdown table rows and section headers are preserved during chunking to prevent disconnected numerical data from losing its semantic context.
