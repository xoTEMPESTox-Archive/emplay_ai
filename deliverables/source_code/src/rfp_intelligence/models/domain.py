"""Core domain models matching the RFP assignment requirements."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Document classification types."""

    BID_PAGE = "bid_page"
    RFP = "rfp"
    ADDENDUM = "addendum"
    SPECS = "specs"
    AFFIDAVIT = "affidavit"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """Metadata attached to ingested documents and chunks."""

    bid_id: str = Field(description="Identifier for the bid folder, e.g. Bid1, Bid2")
    file_name: str = Field(description="Original file name")
    doc_type: DocType = Field(default=DocType.OTHER, description="Classified document type")
    addendum_number: Optional[int] = Field(
        default=None, description="Addendum sequence number if applicable"
    )
    page_number: Optional[int] = Field(
        default=None, description="1-indexed page number if applicable"
    )
    doc_date: Optional[str] = Field(
        default=None, description="Document issue/publication date"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary additional metadata"
    )


class DocumentChunk(BaseModel):
    """Text chunk extracted and prepared for vector/keyword indexing."""

    chunk_id: str = Field(description="Unique chunk identifier")
    text: str = Field(description="Chunk textual content")
    metadata: DocumentMetadata = Field(description="Source document metadata")
    token_count: Optional[int] = Field(
        default=None, description="Estimated token count"
    )


class SourceCitation(BaseModel):
    """Source provenance citation verifying an extracted field or answer."""

    file: str = Field(description="Source document filename")
    page: Optional[int] = Field(default=None, description="Page number where evidence appears")
    chunk_id: Optional[str] = Field(default=None, description="Indexed chunk ID if available")
    snippet: Optional[str] = Field(
        default=None, description="Exemplary quote or snippet supporting the statement"
    )


class ExtractedField(BaseModel):
    """An individual extracted field with provenance, confidence, and audit notes."""

    value: Optional[Any] = Field(
        default=None,
        description="Extracted value, or null if not found in documents",
    )
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Source citations supporting the extracted value",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Explanation, addendum override notes, or 'Not found in documents'",
    )


class AddendumChange(BaseModel):
    """Change log entry recording modifications made by addendums."""

    field_name: str = Field(description="Name of the affected field")
    original_value: Optional[str] = Field(
        default=None, description="Value prior to this addendum"
    )
    updated_value: Optional[str] = Field(
        default=None, description="Updated value specified in addendum"
    )
    source_addendum: str = Field(description="Filename or identifier of the addendum")
    reason: Optional[str] = Field(
        default=None, description="Context or reason stated for the amendment"
    )


class ValidationSummary(BaseModel):
    """Validation report summary for extracted bid fields."""

    passed: int = Field(default=0, ge=0, description="Count of passed fields")
    failed: int = Field(default=0, ge=0, description="Count of failed validation checks")
    not_found: int = Field(
        default=0, ge=0, description="Count of fields explicitly not found in documents"
    )
    issues: List[str] = Field(
        default_factory=list, description="Validation failure details and critique notes"
    )


class BidExtractionResult(BaseModel):
    """Full structured extraction output for a single bid."""

    bid_id: str = Field(description="Identifier for the bid")
    fields: Dict[str, ExtractedField] = Field(
        description="Map of field name to extracted field data"
    )
    addendum_changes: List[AddendumChange] = Field(
        default_factory=list,
        description="Tracked changes overridden by addendums",
    )
    validation: ValidationSummary = Field(
        default_factory=ValidationSummary,
        description="Validation outcome metrics",
    )


class SearchQuery(BaseModel):
    """Request model for retrieval and hybrid search."""

    q: str = Field(description="Search query string")
    bid_id: Optional[str] = Field(
        default=None, description="Optional bid_id filter"
    )
    doc_type: Optional[str] = Field(
        default=None, description="Optional document type filter"
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")


class SearchResult(BaseModel):
    """Search retrieval hit with citation provenance and relevance score."""

    chunk_id: str
    text: str
    score: float
    citation: SourceCitation
    metadata: DocumentMetadata


class QuestionAnswerResult(BaseModel):
    """Structured response for Q&A mode."""

    question: str
    answer: str
    citations: List[SourceCitation] = Field(default_factory=list)


# The 20 mandatory extraction fields from Assignment Section 8
REQUIRED_RFP_FIELDS: List[str] = [
    "Bid Number",
    "Title",
    "Due Date",
    "Bid Submission Type",
    "Term of Bid",
    "Pre Bid Meeting",
    "Installation",
    "Bid Bond Requirement",
    "Delivery Date",
    "Payment Terms",
    "Any Additional Documentation Required",
    "MFG for Registration",
    "Contract or Cooperative to use",
    "Model_no",
    "Part_no",
    "Product",
    "contact_info",
    "company_name",
    "Bid Summary",
    "Product Specification",
]
