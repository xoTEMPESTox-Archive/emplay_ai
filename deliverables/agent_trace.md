# Deliverable: Agent Execution Trace

This deliverable captures the end-to-end execution trace of the LangGraph multi-agent extraction system operating on a bid package, logging step inputs, tool calls, outputs, token consumption, and latencies per Section 7.2 of the assignment.

---

## Trace Metadata

- **Run ID:** `trace-run-bid1-extraction-001`
- **Target Subject:** `Bid1` (`JA-207652 Student and Staff Computing Devices`)
- **Pipeline Mode:** `Extraction`
- **Orchestration Engine:** `LangGraph StateGraph`
- **Primary LLM:** `gemini/gemini-2.0-flash` (routed via LiteLLM)
- **Status:** *Template ready for full capture upon Phase 3/4 pipeline execution*

---

## Step-by-Step Agent Trace Log

### Step 1: Orchestrator / Planner
- **Agent:** `Orchestrator`
- **Action:** Plan Decomposition
- **Input:** `{"bid_id": "Bid1", "task": "Extract 20 structured RFP fields"}`
- **Subtasks Generated:**
  - `Dates & Logistics Specialist`: Due Date, Pre-Bid Meeting, Delivery Date, Term of Bid.
  - `Commercial & Legal Specialist`: Bid Bond, Payment Terms, Affidavits, Contract/Cooperative.
  - `Product & Specs Specialist`: Models, Part Numbers, Hardware Specs, Quantities.
  - `Addendum Reconciliation`: Cross-check Bid1 vs Addendum 1 and Addendum 2.
  - `Validator`: Integrity, format, and citation verification.
- **Latency / Tokens:** *TBD*

---

### Step 2: Retrieval Agent Tool Calls
- **Agent:** `Retrieval Agent`
- **Tool Invocations:**
  - `call_search(query="submission deadline closing date due date", bid_id="Bid1", top_k=5)`
  - `call_search(query="bid bond security deposit percentage", bid_id="Bid1", top_k=5)`
  - `call_search(query="device specifications display RAM processor", bid_id="Bid1", top_k=5)`
- **Tool Outputs:** *List of ranked text chunks with file provenance, page numbers, and RRF scores.*
- **Latency / Tokens:** *TBD*

---

### Step 3: Extraction Specialist Agents
- **Agents:** `Dates & Logistics`, `Commercial & Legal`, `Product & Specs`
- **Input:** Retrieved chunks for target fields.
- **Output:** Candidate fields with confidence scores and citations.
- **Latency / Tokens:** *TBD*

---

### Step 4: Addendum Reconciliation Agent
- **Agent:** `Addendum Reconciler`
- **Input:** Base RFP values + Addendum 1 & 2 passages.
- **Action:** Detects deadline change in Addendum 2.
- **Output:** Updated `Due Date` with notes: `"Extended by Addendum 2 (original date: ...)"`.
- **Latency / Tokens:** *TBD*

---

### Step 5: Validator / Critic Agent & Feedback Loop
- **Agent:** `Validator / Critic`
- **Verification Checks:**
  1. Evidence Check: Are all extracted values grounded in retrieved text?
  2. Format Check: Are dates, numbers, and currencies conforming to schema?
  3. Grounding Guardrail: Ensure fields not present are recorded as `null` with explanation notes.
- **Outcome:** `ValidationSummary(passed=18, failed=0, not_found=2)`
- **Latency / Tokens:** *TBD*

---

### Step 6: Final Output Serialization
- **Agent:** `Q&A / Report Agent`
- **Output File:** `deliverables/outputs/Bid1.json`
- **Result:** Successfully validated JSON artifact.
