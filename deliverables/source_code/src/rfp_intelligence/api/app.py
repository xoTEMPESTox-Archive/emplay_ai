"""FastAPI REST application exposing Search, Ingestion, and Q&A endpoints."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from rfp_intelligence.config import REPO_ROOT
from rfp_intelligence.ingestion.parser import IngestionPipeline
from rfp_intelligence.models.domain import (
    QuestionAnswerResult,
    SearchQuery,
    SearchResult,
    SourceCitation,
)
from rfp_intelligence.search.engine import HybridSearchEngine
from rfp_intelligence.utils.llm import get_completion
from rfp_intelligence.utils.metrics import tracker
from rfp_intelligence.utils.semantic_cache import semantic_cache

app = FastAPI(
    title="RFP Intelligence Platform API",
    description="REST API for hybrid RFP document retrieval and multi-agent extraction.",
    version="0.1.0",
)

# Shared instances
search_engine = HybridSearchEngine()
ingestion_pipeline = IngestionPipeline()


class IndexRequest(BaseModel):
    bid_folder: str = Field(description="Path to bid directory to ingest and index")
    bid_id: Optional[str] = Field(default=None, description="Optional custom bid identifier")


class AskRequest(BaseModel):
    query: str = Field(description="Natural-language question")
    bid_id: Optional[str] = Field(
        default=None, description="Optional bid_id to restrict question context"
    )
    top_k: int = Field(default=5, description="Number of evidence chunks to retrieve")


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "rfp-intelligence"}


@app.get("/metrics", tags=["System"])
def get_metrics() -> Dict[str, Any]:
    """Return latency, token consumption, and cache metrics."""
    return tracker.summary()


@app.post("/index", tags=["Search Engine"])
def index_bid(request: IndexRequest) -> Dict[str, Any]:
    """Index an RFP bid folder into vector and BM25 search indices."""
    folder_path = Path(request.bid_folder)
    if not folder_path.is_absolute():
        folder_path = REPO_ROOT / folder_path

    if not folder_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Bid folder does not exist: {folder_path}"
        )

    try:
        chunks = ingestion_pipeline.ingest_bid_folder(
            folder_path, bid_id=request.bid_id
        )
        indexed_count = search_engine.index_chunks(chunks)
        return {
            "status": "success",
            "bid_folder": str(folder_path),
            "chunks_extracted": len(chunks),
            "chunks_indexed": indexed_count,
            "total_chunks_in_index": search_engine.collection.count(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=List[SearchResult], tags=["Search Engine"])
def search(
    q: str = Query(..., description="Query text"),
    bid_id: Optional[str] = Query(None, description="Optional bid identifier filter"),
    doc_type: Optional[str] = Query(None, description="Optional doc type filter"),
    top_k: int = Query(5, ge=1, le=50, description="Max results"),
) -> List[SearchResult]:
    """Search indexed documents using hybrid retrieval (Dense Vector + BM25 with RRF)."""
    search_q = SearchQuery(q=q, bid_id=bid_id, doc_type=doc_type, top_k=top_k)
    return search_engine.search(search_q)


@app.post("/ask", response_model=QuestionAnswerResult, tags=["Multi-Agent System"])
def ask_question(request: AskRequest) -> QuestionAnswerResult:
    """Answer questions over bids grounded with exact citations."""
    search_q = SearchQuery(q=request.query, bid_id=request.bid_id, top_k=request.top_k)
    hits = search_engine.search(search_q)

    if not hits:
        return QuestionAnswerResult(
            question=request.query,
            answer="Not found in documents. No matching evidence chunks were retrieved.",
            citations=[],
        )

    context_snippets = []
    citations: List[SourceCitation] = []
    for h in hits:
        context_snippets.append(
            f"[Source: {h.citation.file}, Page: {h.citation.page or 'N/A'}]\n{h.text}"
        )
        citations.append(h.citation)

    evidence_block = "\n\n---\n\n".join(context_snippets)

    prompt = (
        f"Answer the user question strictly using only the retrieved evidence below.\n"
        f"Always cite the source document and page number for facts.\n"
        f"If the information is not present, reply 'Not found in documents'.\n\n"
        f"EVIDENCE:\n{evidence_block}\n\n"
        f"QUESTION: {request.query}\n\n"
        f"ANSWER:"
    )

    answer = get_completion(
        prompt,
        system_prompt="You are an expert procurement and RFP intelligence analyst. Ground every statement in evidence.",
        timeout=30,
    )

    return QuestionAnswerResult(
        question=request.query,
        answer=answer,
        citations=citations,
    )
