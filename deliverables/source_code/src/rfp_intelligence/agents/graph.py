"""Multi-agent orchestration workflow built on LangGraph StateGraph."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph

from rfp_intelligence.agents.reconciliation import AddendumReconciliationAgent
from rfp_intelligence.agents.specialists import (
    extract_commercial_and_legal,
    extract_dates_and_logistics,
    extract_product_and_specs,
)
from rfp_intelligence.agents.state import AgentState
from rfp_intelligence.agents.validator import ValidatorAgent
from rfp_intelligence.config import REPO_ROOT, settings
from rfp_intelligence.ingestion.parser import IngestionPipeline
from rfp_intelligence.models.domain import (
    BidExtractionResult,
    ExtractedField,
    QuestionAnswerResult,
    REQUIRED_RFP_FIELDS,
    SearchQuery,
    SourceCitation,
)
from rfp_intelligence.search.engine import HybridSearchEngine
from rfp_intelligence.utils.llm import get_completion
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agents.graph")

# Search and Ingestion singletons
search_engine = HybridSearchEngine()
ingestion_pipeline = IngestionPipeline()
reconciler = AddendumReconciliationAgent()
validator = ValidatorAgent()


def planner_node(state: AgentState) -> Dict[str, Any]:
    """Orchestrator plan generation node."""
    mode = state.get("mode", "extraction")
    bid_id = state.get("bid_id", "UnknownBid")
    logger.info("Planner node executing for %s in %s mode", bid_id, mode)

    if mode == "qa":
        plan = [f"Retrieve relevant evidence for query: {state.get('user_goal')}", "Synthesize cited answer"]
        queries = [state.get("user_goal", "")]
    else:
        plan = [
            "1. Retrieve evidence across Dates, Legal, and Product Specs",
            "2. Run extraction specialists",
            "3. Reconcile addendum amendments",
            "4. Validate evidence grounding and retry if rejected",
            "5. Export structured JSON",
        ]
        # Query formulation for target fields
        queries = [
            f"{bid_id} solicitation number bid identifier title issuing agency",
            f"{bid_id} submission deadline closing due date time zone",
            f"{bid_id} bid submission type electronic sealed paper portal",
            f"{bid_id} pre-bid meeting conference mandatory date location",
            f"{bid_id} term of bid contract duration renewal options",
            f"{bid_id} installation deployment imaging services required",
            f"{bid_id} bid bond security surety deposit amount percentage",
            f"{bid_id} delivery date window delivery schedule after award",
            f"{bid_id} payment terms net 30 invoicing conditions",
            f"{bid_id} required affidavits forms certificates mercury contract",
            f"{bid_id} manufacturer registration authorized partner Dell Lenovo",
            f"{bid_id} cooperative contract vehicle to use",
            f"{bid_id} model number part SKU product name quantity",
            f"{bid_id} procurement contact email phone name",
            f"{bid_id} technical product specifications CPU RAM storage display",
            f"{bid_id} addendum 1 addendum 2 changes extensions",
        ]

    return {
        "plan": plan,
        "search_queries": queries,
        "retry_count": state.get("retry_count", 0),
        "errors": state.get("errors", []),
    }


def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Retrieval Agent node calling Hybrid Search Engine."""
    bid_id = state.get("bid_id")
    queries = state.get("search_queries", [])
    logger.info("Retrieval agent executing %d search queries for bid %s", len(queries), bid_id)

    all_evidence = list(state.get("retrieved_evidence", []))
    seen_chunk_ids = {c.get("chunk_id") for c in all_evidence}

    for q in queries:
        query_obj = SearchQuery(q=q, bid_id=bid_id, top_k=4)
        hits = search_engine.search(query_obj)
        for h in hits:
            if h.chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(h.chunk_id)
                all_evidence.append(
                    {
                        "chunk_id": h.chunk_id,
                        "text": h.text,
                        "metadata": h.metadata.model_dump(),
                    }
                )

    return {"retrieved_evidence": all_evidence}


def extraction_node(state: AgentState) -> Dict[str, Any]:
    """Extraction Specialists node parsing the 20 structured fields."""
    bid_id = state.get("bid_id", "")
    all_evidence = state.get("retrieved_evidence", [])
    logger.info("Extraction specialists processing %d evidence chunks for %s", len(all_evidence), bid_id)

    # Map target field queries to evidence
    evidence_map: Dict[str, List[Dict[str, Any]]] = {}
    for f in REQUIRED_RFP_FIELDS:
        terms = f.lower().split()
        matched_chunks = []
        for c in all_evidence:
            text_lower = c.get("text", "").lower()
            if any(term in text_lower for term in terms):
                matched_chunks.append(c)
        evidence_map[f] = matched_chunks if matched_chunks else all_evidence[:4]

    # Specialists extract fields
    draft_fields = dict(state.get("draft_fields", {}))
    draft_fields.update(extract_dates_and_logistics(evidence_map))
    draft_fields.update(extract_commercial_and_legal(evidence_map))
    draft_fields.update(extract_product_and_specs(evidence_map))

    return {"draft_fields": draft_fields}


def reconciliation_node(state: AgentState) -> Dict[str, Any]:
    """Addendum Reconciliation Agent node detecting overrides."""
    draft_fields = state.get("draft_fields", {})
    evidence = state.get("retrieved_evidence", [])
    updated_fields, changes = reconciler.reconcile(draft_fields, evidence)

    all_changes = list(state.get("addendum_changes", [])) + changes
    return {"draft_fields": updated_fields, "addendum_changes": all_changes}


def validation_node(state: AgentState) -> Dict[str, Any]:
    """Validator / Critic Agent node inspecting evidence grounding."""
    draft_fields = state.get("draft_fields", {})
    summary, failed_fields = validator.validate_fields(draft_fields)

    return {
        "validation_report": summary.model_dump(),
        "failed_fields": failed_fields,
    }


def should_retry(state: AgentState) -> str:
    """Conditional router: loop back to retrieval if fields failed, else finish."""
    failed = state.get("failed_fields", [])
    retry_count = state.get("retry_count", 0)
    max_retries = settings.max_validation_retries

    if failed and retry_count < max_retries:
        logger.warning(
            "Validation failed for fields %s. Retrying retrieval/extraction (%d/%d)...",
            failed,
            retry_count + 1,
            max_retries,
        )
        return "retry"
    return "finish"


def retry_prep_node(state: AgentState) -> Dict[str, Any]:
    """Prepare more targeted search queries for failed fields before re-retrieval."""
    failed = state.get("failed_fields", [])
    bid_id = state.get("bid_id", "")
    new_queries = [f"{bid_id} {f} specific section details" for f in failed]
    return {
        "search_queries": new_queries,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def report_node(state: AgentState) -> Dict[str, Any]:
    """Final output synthesis node."""
    mode = state.get("mode", "extraction")
    bid_id = state.get("bid_id", "UnknownBid")

    if mode == "qa":
        goal = state.get("user_goal", "")
        evidence = state.get("retrieved_evidence", [])
        snippets = []
        citations = []
        for e in evidence[:5]:
            meta = e.get("metadata", {})
            file_name = meta.get("file_name", "document")
            page_no = meta.get("page_number")
            citations.append(
                SourceCitation(
                    file=file_name,
                    page=page_no if page_no != -1 else None,
                    snippet=e.get("text", "")[:200] + "...",
                )
            )
            snippets.append(f"[File: {file_name}, Page: {page_no}]\n{e.get('text', '')}")

        prompt = (
            f"Answer the question strictly from the evidence.\n"
            f"QUESTION: {goal}\n\n"
            f"EVIDENCE:\n" + "\n\n---\n\n".join(snippets) + "\n\n"
            f"ANSWER WITH CITATIONS:"
        )
        ans_text = get_completion(prompt)
        qa_res = QuestionAnswerResult(
            question=goal,
            answer=ans_text,
            citations=citations,
        )
        return {"final_output": qa_res.model_dump()}

    # Extraction mode: assemble BidExtractionResult
    fields_dict: Dict[str, ExtractedField] = state.get("draft_fields", {})
    addendum_changes = state.get("addendum_changes", [])
    validation_report = state.get("validation_report", {})

    result = BidExtractionResult(
        bid_id=bid_id,
        fields=fields_dict,
        addendum_changes=addendum_changes,
        validation=validation_report,
    )
    return {"final_output": result.model_dump()}


# Build LangGraph StateGraph
graph_builder = StateGraph(AgentState)

graph_builder.add_node("planner", planner_node)
graph_builder.add_node("retriever", retrieval_node)
graph_builder.add_node("extractor", extraction_node)
graph_builder.add_node("reconciler", reconciliation_node)
graph_builder.add_node("validator", validation_node)
graph_builder.add_node("retry_prep", retry_prep_node)
graph_builder.add_node("reporter", report_node)

graph_builder.set_entry_point("planner")
graph_builder.add_edge("planner", "retriever")
graph_builder.add_edge("retriever", "extractor")
graph_builder.add_edge("extractor", "reconciler")
graph_builder.add_edge("reconciler", "validator")

graph_builder.add_conditional_edges(
    "validator",
    should_retry,
    {
        "retry": "retry_prep",
        "finish": "reporter",
    },
)
graph_builder.add_edge("retry_prep", "retriever")
graph_builder.add_edge("reporter", END)

# Compiled graph
agent_graph = graph_builder.compile()


def run_extraction_pipeline(bid_folder: Path, bid_id: Optional[str] = None) -> BidExtractionResult:
    """Run full multi-agent extraction pipeline over a bid folder."""
    folder = Path(bid_folder)
    target_bid_id = bid_id or folder.name

    # Step 1: Ensure documents are ingested and indexed
    chunks = ingestion_pipeline.ingest_bid_folder(folder, bid_id=target_bid_id)
    search_engine.index_chunks(chunks)

    # Step 2: Initialize AgentState and run LangGraph
    initial_state: AgentState = {
        "bid_id": target_bid_id,
        "user_goal": f"Extract all 20 required fields for {target_bid_id}",
        "mode": "extraction",
        "retry_count": 0,
        "errors": [],
    }

    final_state = agent_graph.invoke(initial_state)
    output_dict = final_state.get("final_output", {})
    return BidExtractionResult(**output_dict)


def run_qa_pipeline(query: str, bid_id: Optional[str] = None) -> QuestionAnswerResult:
    """Run Q&A agent over indexed documents with citations."""
    initial_state: AgentState = {
        "bid_id": bid_id or "",
        "user_goal": query,
        "mode": "qa",
        "retry_count": 0,
        "errors": [],
    }
    final_state = agent_graph.invoke(initial_state)
    output_dict = final_state.get("final_output", {})
    return QuestionAnswerResult(**output_dict)
