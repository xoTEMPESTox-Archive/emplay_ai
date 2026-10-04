"""
Active Agent Tools for iterative retrieval, addendum reconciliation, and listwise reranking.
"""

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rfp_intelligence.models.domain import DocType, SearchQuery, SearchResult
from rfp_intelligence.search.engine import HybridSearchEngine, rerank_passages_listwise
from rfp_intelligence.search.decomposition import decompose_query, DecomposedQueries
from rfp_intelligence.utils.llm import get_completion
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agent_tools")


class ReconciliationResult(BaseModel):
    has_conflict: bool = Field(description="True if addendum changes or supersedes base document")
    superseded_field: str = Field(description="Name of the affected RFP field")
    original_value: Optional[str] = Field(default=None, description="Original term or date in base RFP")
    overridden_value: Optional[str] = Field(default=None, description="New term or extended date in addendum")
    explanation: str = Field(description="Reasoning explaining the change")
    citation_file: str = Field(description="Addendum file name")
    citation_page: Optional[int] = Field(default=None, description="Page number of the amendment")


class AgentTools:
    """Suite of discrete tools callable by multi-agent workflows and interactive chat."""

    def __init__(self, engine: Optional[HybridSearchEngine] = None) -> None:
        self.engine = engine or HybridSearchEngine()

    def search_base_rfp(
        self, query: str, bid_id: Optional[str] = None, top_k: int = 5
    ) -> List[SearchResult]:
        """Search primary bid documents (base RFP, specifications, bid portal pages)."""
        sq = SearchQuery(q=query, bid_id=bid_id, top_k=top_k)
        # Exclude addenda to get baseline provisions
        hits = self.engine.search(sq, use_reranker=True)
        return [h for h in hits if not h.metadata.is_amendment][:top_k]

    def search_addenda(
        self, query: str, bid_id: Optional[str] = None, top_k: int = 5
    ) -> List[SearchResult]:
        """Search strictly across Addenda, Amendments, and Clarification notices."""
        sq = SearchQuery(q=query, bid_id=bid_id, doc_type=DocType.ADDENDUM.value, top_k=top_k)
        hits = self.engine.search(sq, use_reranker=True)
        return hits[:top_k]

    def reconcile_conflicts(
        self, base_statement: str, addendum_statement: str, topic: str = "Requirement"
    ) -> ReconciliationResult:
        """Analyze base and addendum statements with an LLM to resolve contradictions."""
        prompt = (
            f"Topic: {topic}\n\n"
            f"Base RFP Statement:\n\"{base_statement}\"\n\n"
            f"Addendum / Amendment Statement:\n\"{addendum_statement}\"\n\n"
            "Determine if the addendum changes, extends, or supersedes the base statement.\n"
            "Return a valid JSON object matching this schema:\n"
            "{\n"
            "  \"has_conflict\": true,\n"
            "  \"superseded_field\": \"name of field, e.g. Due Date\",\n"
            "  \"original_value\": \"original term\",\n"
            "  \"overridden_value\": \"new extended term\",\n"
            "  \"explanation\": \"clear explanation of the override\"\n"
            "}"
        )
        try:
            resp = get_completion(
                prompt=prompt,
                system_prompt="You are a legal RFP addendum reconciliation agent. Output JSON only.",
                json_mode=True,
                timeout=12,
            )
            data = json.loads(resp)
            return ReconciliationResult(
                has_conflict=bool(data.get("has_conflict", False)),
                superseded_field=data.get("superseded_field", topic),
                original_value=data.get("original_value"),
                overridden_value=data.get("overridden_value"),
                explanation=data.get("explanation", "Addendum supersedes base provision."),
                citation_file="Addendum Document",
                citation_page=1,
            )
        except Exception as e:
            logger.warning("Agent reconciliation parsing error: %s", e)
            return ReconciliationResult(
                has_conflict=False,
                superseded_field=topic,
                explanation="No conflict identified.",
                citation_file="",
            )

    def run_agentic_rag(
        self,
        question: str,
        bid_id: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full agentic RAG loop: Decompose -> Multi-Query Retrieve -> Addenda Check -> Rerank -> Generate."""
        catalog = self.engine.get_bid_catalog()
        
        # 1. Multi-Query Search with dynamic catalog and balanced partitioning
        candidates, decomposed = self.engine.multi_query_search(
            question=question,
            bid_id=bid_id,
            top_k=10,
            use_reranker=True,
            model=model,
            api_key=api_key,
        )
        target_bids = [bid_id] if bid_id else decomposed.target_bids
        is_comparative = decomposed.is_comparative and len(target_bids) > 1

        # 2. Active Addenda Tool Check: Check for superseding addenda across relevant bids
        q_lower = question.lower()
        if decomposed.addendum_query or any(w in q_lower for w in ["deadline", "due", "date", "submission", "schedule", "addendum", "amendment"]):
            existing_ids = {c.chunk_id for c in candidates}
            bids_to_check = target_bids if target_bids else [None]
            for b in bids_to_check:
                addenda_hits = self.search_addenda(query=question, bid_id=b, top_k=3)
                for ah in addenda_hits:
                    if ah.chunk_id not in existing_ids:
                        candidates.append(ah)
                        existing_ids.add(ah.chunk_id)

        # 3. Listwise Reranking / Evidentiary Filtering (allow more passages if comparative)
        eval_top_k = 6 if is_comparative else 4
        top_passages = rerank_passages_listwise(
            question=question,
            candidates=candidates,
            top_k=eval_top_k,
            model=model,
            api_key=api_key,
        )

        # 4. Format Context with Explicit Bid Provenance and Document Labels
        context_parts = []
        citations_data = []
        for p in top_passages:
            bid_label = p.metadata.bid_id or "General"
            bid_title = catalog.get(bid_label, {}).get("title", "")
            title_tag = f" ({bid_title})" if bid_title and bid_title != bid_label else ""
            context_parts.append(
                f"[Bid: {bid_label}{title_tag} | Document: {p.citation.file} | Page {p.citation.page or 'N/A'}]:\n{p.text}"
            )
            citations_data.append({
                "bid": bid_label,
                "file": p.citation.file,
                "page": p.citation.page or "N/A",
                "snippet": p.citation.snippet[:200],
            })

        context_block = "\n\n---\n\n".join(context_parts)
        system_instruction = (
            "You are an expert procurement and RFP intelligence analyst. "
            "Answer the question directly, factually, and accurately using only the provided context. "
            "Each source passage is explicitly labeled with its associated Bid identifier and Solicitation title (e.g. [Bid: Bid2 (Dell Laptops w/ Extended Warranty) | ...]). "
            "When answering questions referencing a solicitation by subject (e.g. 'the Dell laptop bid') or by ID (e.g. 'Bid1'), connect the question to the matching Bid passages and state the facts clearly. "
            "If asked for a comparison, provide a clear, structured breakdown or Markdown table comparing the bids. "
            "Explicitly highlight any addendum overrides (e.g. deadline extensions) if present. "
            "At the end of your response, list the citations under a '**Sources:**' heading."
        )
        user_prompt = f"Context:\n{context_block}\n\nQuestion: {question}\n\nAnswer with citations:"

        answer = get_completion(
            prompt=user_prompt,
            system_prompt=system_instruction,
            model=model,
            api_key=api_key,
        )

        # Ensure Sources are cleanly formatted if model didn't include them
        if "source" not in answer.lower() and citations_data:
            unique_sources = []
            seen = set()
            for c in citations_data:
                key = (c["bid"], c["file"], c["page"])
                if key not in seen:
                    seen.add(key)
                    unique_sources.append(f"- **[{c['bid']}] {c['file']}** (Page {c['page']})")
            answer += "\n\n**Sources:**\n" + "\n".join(unique_sources)

        return {
            "question": question,
            "answer": answer,
            "sub_queries": decomposed.sub_queries,
            "target_bid": decomposed.target_bid,
            "target_bids": decomposed.target_bids,
            "is_comparative": is_comparative,
            "passages": top_passages,
            "citations": citations_data,
        }

