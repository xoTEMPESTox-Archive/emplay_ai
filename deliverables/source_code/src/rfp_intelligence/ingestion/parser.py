"""Document parsing interfaces and placeholders for RFP ingestion."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from rfp_intelligence.models.domain import DocumentChunk, DocumentMetadata


class BaseDocumentParser(ABC):
    """Abstract base class for document format parsers (HTML, PDF)."""

    @abstractmethod
    def parse(self, file_path: Path, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Parse a document file into normalized document chunks with metadata.

        Args:
            file_path: Absolute or relative path to the file.
            metadata: Base metadata associated with the file.

        Returns:
            List of DocumentChunk instances.
        """
        raise NotImplementedError("TODO: Implement in Phase 1 (Document Ingestion)")


class IngestionPipeline:
    """Pipeline orchestrating bid folder discovery, parsing, and chunk generation."""

    def __init__(self, parser: BaseDocumentParser = None) -> None:
        self.parser = parser

    def ingest_bid_folder(self, folder_path: Path) -> List[DocumentChunk]:
        """Discover and ingest all supported documents in a bid folder.

        Args:
            folder_path: Path to the bid directory.

        Returns:
            List of generated DocumentChunk instances ready for indexing.
        """
        # TODO: Phase 1 implementation (folder discovery, metadata extraction, parsing)
        raise NotImplementedError("TODO: Implement in Phase 1 (Document Ingestion)")
