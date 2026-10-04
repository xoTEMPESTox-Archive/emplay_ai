"""Shared state definition for the multi-agent system (LangGraph compatible)."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across all nodes in the agent graph."""

    # Context & Goal
    bid_id: str
    user_goal: str
    mode: str  # "extraction" or "qa"

    # Execution Plan
    plan: List[str]

    # Retrieval State
    search_queries: List[str]
    retrieved_evidence: List[Dict[str, Any]]

    # Extraction State
    draft_fields: Dict[str, Any]
    addendum_changes: List[Dict[str, Any]]

    # Validation State & Retry Loop
    validation_report: Dict[str, Any]
    failed_fields: List[str]
    retry_count: int

    # Final Output
    final_output: Optional[Dict[str, Any]]
    errors: List[str]
