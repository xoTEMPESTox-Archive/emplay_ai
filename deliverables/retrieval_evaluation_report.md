# Deliverable: Retrieval Evaluation Report

This report documents the quantitative retrieval evaluation framework designed to benchmark search quality across **Bid1** and **Bid2**, comparing multiple retrieval configurations in accordance with Section 6.4 of the assignment.

---

## 1. Evaluation Methodology

The search engine is evaluated using a curated benchmark of **16 ground-truth questions** targeting diverse information types (exact part/bid numbers, deadlines, legal terms, hardware specifications, and addendum overrides).

### Evaluation Metrics
- **Recall@k (k = 3, 5)**: Proportion of queries where the relevant ground-truth passage appears within the top $k$ retrieved chunks.
- **MRR (Mean Reciprocal Rank)**: $\frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$, measuring how high the first relevant chunk appears in ranking.

---

## 2. Benchmark Evaluation Question Set

| # | Bid | Query / Question | Target Document | Expected Evidence / Concept |
|---|---|---|---|---|
| 1 | Bid1 | What is the solicitation or bid number? | HTML / RFP Final | `JA-207652` |
| 2 | Bid1 | What was the original submission deadline? | RFP Final | Original due date prior to extensions |
| 3 | Bid1 | What is the final submission due date after Addendum 2? | Addendum 2 | Extended submission deadline with timezone |
| 4 | Bid1 | Is a bid bond or deposit required? | RFP Final | Bond requirement status or percentage |
| 5 | Bid1 | What are the mandatory device specifications (display, processor)? | RFP Final | Computing device technical requirements |
| 6 | Bid1 | Are installation or deployment services required? | RFP Final | Services scope and deployment expectations |
| 7 | Bid1 | What changes were introduced specifically in Addendum 1? | Addendum 1 | Timeline or specification clarification items |
| 8 | Bid1 | Who is the primary procurement contact? | HTML BidNet page | Contact name, email, phone |
| 9 | Bid2 | What is the bid number for the Dell laptop solicitation? | HTML / PORFP | Solicitation identifier |
| 10 | Bid2 | Which specific affidavits are required with the bid submission? | Contract / Mercury Affidavit | Contract Affidavit and Mercury Affidavit requirements |
| 11 | Bid2 | What processor, RAM, and SSD specs are specified for Dell laptops? | Dell_Laptop_Specs.pdf | Exact hardware specifications |
| 12 | Bid2 | What warranty coverage is mandated for the laptops? | Specs / PORFP | Extended warranty duration and coverage |
| 13 | Bid2 | What are the payment terms specified? | PORFP | Payment schedule (e.g. Net 30) |
| 14 | Bid2 | Is attendance at a pre-bid conference mandatory? | HTML / PORFP | Pre-bid meeting details or "None" |
| 15 | Bid2 | What manufacturer registration or authorization is required? | PORFP | Manufacturer authorization requirements |
| 16 | Both | Compare the warranty requirements between Bid1 and Bid2. | Both Bids | Cross-bid comparative warranty terms |

---

## 3. Comparative Benchmark Results

*Note: Baseline benchmarks will be populated upon running Phase 5 evaluation.*

| Retrieval Strategy | Recall@3 | Recall@5 | MRR | Notes |
|---|---|---|---|---|
| **1. Dense Vector Only** (`gemini/text-embedding-004`) | *TBD (Phase 5)* | *TBD (Phase 5)* | *TBD (Phase 5)* | Baseline semantic vector search |
| **2. Hybrid Search** (Vector + BM25 with RRF) | *TBD (Phase 5)* | *TBD (Phase 5)* | *TBD (Phase 5)* | Improved on exact solicitation & model IDs |
| **3. Hybrid Search + Reranker** | *TBD (Phase 5)* | *TBD (Phase 5)* | *TBD (Phase 5)* | Precision optimization on top-ranked passages |

---

## 4. Key Findings & Analysis

*(Detailed findings and analysis will be logged here during Phase 5 execution).*
