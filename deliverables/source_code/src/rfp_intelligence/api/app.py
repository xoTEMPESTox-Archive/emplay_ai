"""FastAPI REST application exposing Search and Q&A endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from rfp_intelligence.models.domain import QuestionAnswerResult, SearchResult

app = FastAPI(
    title="RFP Intelligence Platform API",
    description="REST API for hybrid RFP document retrieval and multi-agent extraction.",
    version="0.1.0",
)


class IndexRequest(BaseModel):
    bid_folder: str = Field(description="Path to bid directory to ingest and index")


class AskRequest(BaseModel):
    query: str = Field(description="Natural-language question")
    bid_id: Optional[str] = Field(
        default=None, description="Optional bid_id to restrict question context"
    )


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "rfp-intelligence"}


@app.post("/index", tags=["Search Engine"])
def index_bid(request: IndexRequest) -> Dict[str, Any]:
    """Index an RFP bid folder."""
    # TODO: Phase 2 Search Engine implementation
    raise HTTPException(
        status_code=501,
        detail="Indexing pipeline not yet implemented. Planned for Phase 2.",
    )


@app.get("/search", response_model=List[SearchResult], tags=["Search Engine"])
def search(
    q: str = Query(..., description="Query text"),
    bid_id: Optional[str] = Query(None, description="Optional bid identifier filter"),
    top_k: int = Query(5, ge=1, le=50, description="Max results"),
) -> List[SearchResult]:
    """Search indexed documents using hybrid retrieval."""
    # TODO: Phase 2 Search Engine implementation
    raise HTTPException(
        status_code=501,
        detail="Hybrid search not yet implemented. Planned for Phase 2.",
    )


@app.post("/ask", response_model=QuestionAnswerResult, tags=["Multi-Agent System"])
def ask_question(request: AskRequest) -> QuestionAnswerResult:
    """Answer questions over bids with grounded citations."""
    # TODO: Phase 3 Multi-Agent implementation
    raise HTTPException(
        status_code=501,
        detail="Q&A agent system not yet implemented. Planned for Phase 3.",
    )
