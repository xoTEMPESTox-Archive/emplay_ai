"""Query restructuring and sub-query decomposition using LiteLLM."""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rfp_intelligence.utils.llm import get_completion
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.decomposition")


class DecomposedQueries(BaseModel):
    """Structured breakdown of user query for comprehensive RFP retrieval."""
    core_query: str = Field(description="Primary factual subject query")
    addendum_query: Optional[str] = Field(default=None, description="Amendment/override query if time or terms are involved")
    target_bid: Optional[str] = Field(default=None, description="Primary target bid identifier if single-bid, or None if cross-bid/general")
    target_bids: List[str] = Field(default_factory=list, description="Target bid identifiers for single or multi-bid comparative queries")
    is_comparative: bool = Field(default=False, description="True if query compares multiple bids or asks about 'both bids'")
    sub_queries: List[str] = Field(default_factory=list, description="All individual search queries to execute without meta-noise")


def clean_query_text(text: str) -> str:
    """Strip out meta-labels like 'Bid1', 'Bid2', 'vs' that pollute semantic and lexical search."""
    cleaned = re.sub(r"\b(bid\s*[0-9]+|both bids|vs\.?|versus)\b", " ", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else text


def detect_bids_rule_based(question: str, known_bids: Optional[List[str]] = None) -> tuple[List[str], bool]:
    """Heuristic fallback to identify target bids and comparative intent."""
    q_lower = question.lower()
    bids_found = []
    
    # Check explicitly indexed or default bids
    candidate_bids = known_bids or ["Bid1", "Bid2"]
    for b in candidate_bids:
        b_clean = b.lower().replace(" ", "")
        b_spaced = b.lower()
        if re.search(r"\b" + re.escape(b_clean) + r"\b", q_lower) or re.search(r"\b" + re.escape(b_spaced) + r"\b", q_lower):
            if b not in bids_found:
                bids_found.append(b)

    # Subject-based aliases for standard bids if not matched by ID
    if not bids_found:
        if any(term in q_lower for term in ["dell laptop", "dell laptops", "maryland", "porfp", "contract affidavit", "mercury affidavit"]):
            if "Bid2" in candidate_bids:
                bids_found.append("Bid2")
        if any(term in q_lower for term in ["student and staff", "computing devices", "dallas isd", "ja-207652"]):
            if "Bid1" in candidate_bids:
                bids_found.append("Bid1")

    # Check comparative flags
    is_comp = False
    if any(w in q_lower for w in ["both bids", "both the bids", "compare", "comparison", "difference between", " vs ", " vs. ", " versus "]):
        is_comp = True
    if len(bids_found) > 1:
        is_comp = True

    # If user explicitly said "both bids" but didn't list IDs, target all known bids
    if is_comp and not bids_found and candidate_bids:
        bids_found = list(candidate_bids)

    return bids_found, is_comp


DECOMPOSITION_SYSTEM_PROMPT = """You are an expert procurement and RFP search query restructuring specialist.
Your job is to analyze a user's question regarding RFP bids and decompose it for a hybrid RAG search engine.

Key Guidelines:
1. Target Bids: Identify which bid(s) the user refers to based on the available bid catalog.
   - If comparing multiple bids (e.g. 'Bid1 vs Bid2', 'both bids'), set "is_comparative": true and list all target bids.
   - If asking about a single bid (e.g. 'Dell laptop bid', 'Bid1 submission deadline'), list that bid.
   - If general across all bids, set "target_bids": [] and "is_comparative": false.
2. Clean Sub-Queries: Documents contain actual domain vocabulary (e.g. 'processor display RAM specifications', 'submission deadline schedule', 'contract affidavit requirements').
   DO NOT include labels like 'Bid1', 'Bid2', or 'vs' in the sub_queries because those words do not appear in the RFP text!
3. Addendum Overrides: If the question touches deadlines, delivery dates, or changing terms, generate a targeted addendum query.

Output valid JSON matching this schema:
{
  "target_bids": ["Bid1", "Bid2"],
  "is_comparative": true,
  "core_query": "processor RAM display specifications",
  "addendum_query": "addendum extension schedule changes",
  "sub_queries": ["processor RAM display specifications", "hardware technical requirements"]
}
"""


def decompose_query(
    question: str,
    catalog: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> DecomposedQueries:
    """Decompose a natural language query into targeted, vocabulary-aligned search queries."""
    known_bids = list(catalog.keys()) if catalog else ["Bid1", "Bid2"]
    bids_detected, is_comp = detect_bids_rule_based(question, known_bids=known_bids)
    
    cleaned_subject = clean_query_text(question)
    q_lower = question.lower()

    fallback_queries = [cleaned_subject]
    if any(w in q_lower for w in ["deadline", "due", "date", "submission"]):
        fallback_queries.append("due date submission deadline opening date closing schedule")
        fallback_queries.append("addendum extension rescheduled revised date")
    elif any(w in q_lower for w in ["spec", "specs", "ram", "cpu", "processor", "laptop", "display", "storage"]):
        fallback_queries.append("hardware specifications display processor ram storage operating system")
    elif "affidavit" in q_lower:
        fallback_queries.append("contract affidavit mercury affidavit mandatory submission requirement")
    elif "warranty" in q_lower:
        fallback_queries.append("warranty requirements period extended coverage support")
    elif "bond" in q_lower:
        fallback_queries.append("bid bond proposal security deposit cashier check percentage")

    target_bid_scalar = bids_detected[0] if len(bids_detected) == 1 else None

    fallback = DecomposedQueries(
        core_query=cleaned_subject,
        addendum_query="addendum extension revised changes" if ("addend" in q_lower or "date" in q_lower) else None,
        target_bid=target_bid_scalar,
        target_bids=bids_detected,
        is_comparative=is_comp,
        sub_queries=fallback_queries,
    )

    # Format dynamic catalog context for the LLM
    catalog_desc = ""
    if catalog:
        lines = []
        for bid_id, info in catalog.items():
            files_str = ", ".join(info.get("files", [])[:4])
            lines.append(f"- {bid_id}: {info.get('title', 'Solicitation')} (Files: {files_str})")
        catalog_desc = "\nAvailable Bids in Index:\n" + "\n".join(lines)
    else:
        catalog_desc = "\nAvailable Bids in Index:\n- Bid1: Student and Staff Computing Devices (Dallas ISD JA-207652)\n- Bid2: Dell Laptops w/ Extended Warranty (Maryland PORFP)"

    try:
        user_prompt = f"User Question: {question}\n{catalog_desc}\n\nDeconstruct the query into JSON:"
        response_text = get_completion(
            prompt=user_prompt,
            system_prompt=DECOMPOSITION_SYSTEM_PROMPT,
            model=model,
            api_key=api_key,
            json_mode=True,
            timeout=10,
        )
        data = json.loads(response_text)

        target_bids_res = data.get("target_bids", [])
        if not isinstance(target_bids_res, list):
            target_bids_res = [target_bids_res] if target_bids_res else []

        # Merge with rule-based if LLM missed obvious detection
        final_bids = target_bids_res if target_bids_res else bids_detected
        is_comp_res = bool(data.get("is_comparative", is_comp or len(final_bids) > 1))

        sub_qs = data.get("sub_queries", [])
        if not sub_qs:
            sub_qs = [clean_query_text(data.get("core_query", cleaned_subject))]
            if data.get("addendum_query"):
                sub_qs.append(clean_query_text(data["addendum_query"]))

        # Ensure no meta-labels remain in sub-queries
        sanitized_sub_qs = [clean_query_text(sq) for sq in sub_qs if sq.strip()]
        if not sanitized_sub_qs:
            sanitized_sub_qs = fallback_queries

        primary_bid = final_bids[0] if (len(final_bids) == 1 and not is_comp_res) else None

        return DecomposedQueries(
            core_query=clean_query_text(data.get("core_query", cleaned_subject)),
            addendum_query=data.get("addendum_query"),
            target_bid=primary_bid,
            target_bids=final_bids,
            is_comparative=is_comp_res,
            sub_queries=sanitized_sub_qs,
        )
    except Exception as e:
        logger.warning("Query decomposition fell back to rule-based: %s", e)
        return fallback

