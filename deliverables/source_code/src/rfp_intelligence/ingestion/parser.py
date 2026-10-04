"""Document parsing, metadata extraction, and chunking pipeline for RFP ingestion."""

import re
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
from pypdf import PdfReader

from rfp_intelligence.models.domain import (
    DocType,
    DocumentChunk,
    DocumentMetadata,
)
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.ingestion")


def clean_text(text: str) -> str:
    """Normalize whitespace, remove carriage returns, and fix broken hyphenation."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Fix broken hyphenated words at line ends (e.g. "com-\nputing" -> "computing")
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    # Replace multiple newlines with double newline
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple inline whitespace with single space
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def classify_document(file_name: str) -> tuple[DocType, Optional[int]]:
    """Determine DocType and optional addendum number from filename heuristics."""
    name_lower = file_name.lower()

    # Addendum check
    if "addendum" in name_lower:
        match = re.search(r"addendum\s*(\d+)", name_lower)
        num = int(match.group(1)) if match else None
        return DocType.ADDENDUM, num

    # HTML Bid Portal Page
    if name_lower.endswith(".html") or name_lower.endswith(".htm") or "bidnet" in name_lower:
        return DocType.BID_PAGE, None

    # Specifications
    if "spec" in name_lower:
        return DocType.SPECS, None

    # Affidavit
    if "affidavit" in name_lower:
        return DocType.AFFIDAVIT, None

    # RFP or Purchase Order RFP
    if "rfp" in name_lower or "porfp" in name_lower or "final" in name_lower:
        return DocType.RFP, None

    return DocType.OTHER, None


class HTMLDocumentParser:
    """Parser for HTML bid portal pages using BeautifulSoup."""

    def parse(self, file_path: Path, base_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Extract clean text and tables from HTML file."""
        chunks: List[DocumentChunk] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error("Failed to read HTML file %s: %s", file_path, e)
            return chunks

        soup = BeautifulSoup(content, "html.parser")

        # Remove irrelevant tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        # Extract structured key-value tables (e.g. Bid Details table on BidNet)
        extracted_tables_text = []
        for table in soup.find_all("table"):
            rows_text = []
            for row in table.find_all("tr"):
                cols = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                if cols and any(cols):
                    rows_text.append(" | ".join(cols))
            if rows_text:
                extracted_tables_text.append("\n".join(rows_text))

        # Main body text
        body_text = clean_text(soup.get_text(separator="\n"))

        full_text = body_text
        if extracted_tables_text:
            full_text = "\n\n### Extracted Bid Information Tables:\n" + "\n\n".join(extracted_tables_text) + "\n\n" + body_text

        # Chunk the text into manageable windows
        chunks = chunk_text(full_text, base_metadata, page_number=1)
        return chunks


class PDFDocumentParser:
    """Parser for multi-page PDF files using pypdf."""

    def parse(self, file_path: Path, base_metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Extract text page-by-page from PDF."""
        chunks: List[DocumentChunk] = []
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", file_path, e)
            return chunks

        total_pages = len(reader.pages)
        logger.info("Parsing PDF %s (%d pages)", file_path.name, total_pages)

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_raw = page.extract_text() or ""
                cleaned = clean_text(page_raw)
                if not cleaned:
                    logger.debug("Page %d of %s is empty or scanned image", page_idx, file_path.name)
                    continue

                page_meta = base_metadata.model_copy()
                page_meta.page_number = page_idx

                page_chunks = chunk_text(cleaned, page_meta, page_number=page_idx)
                chunks.extend(page_chunks)
            except Exception as e:
                logger.warning("Error reading page %d of %s: %s", page_idx, file_path.name, e)

        return chunks


OPERATIVE_PATTERNS = [
    r"extend\s+(?:the\s+)?(?:due\s+date|deadline)",
    r"rescheduled",
    r"purpose\s+of\s+this\s+addendum",
    r"new\s+due\s+date",
    r"supersedes?",
    r"clarification\s+to\s+specifications",
    r"opening\s+date\s+has\s+been",
]


def is_operative_text(text: str) -> bool:
    """Detect if chunk contains binding amendment or schedule extension clauses."""
    t_lower = text.lower()
    return any(re.search(pat, t_lower) for pat in OPERATIVE_PATTERNS)


def chunk_text(
    text: str,
    metadata: DocumentMetadata,
    page_number: Optional[int] = None,
    chunk_size: int = 750,
    overlap: int = 150,
) -> List[DocumentChunk]:
    """Split text into overlapping chunks, preserving operative clauses and paragraph boundaries."""
    chunks: List[DocumentChunk] = []
    if not text:
        return chunks

    # If addendum page is concise (< 1500 chars), preserve as a single high-salience cohesive chunk
    if metadata.is_amendment and len(text) < 1500:
        chunk_id = f"{metadata.bid_id}_{metadata.file_name}_p{page_number or 1}_c0"
        meta_copy = metadata.model_copy()
        meta_copy.page_number = page_number
        meta_copy.is_operative_clause = is_operative_text(text)
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                metadata=meta_copy,
                token_count=len(text) // 4,
            )
        )
        return chunks

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    current_chunk = ""
    chunk_idx = 0

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunk_id = f"{metadata.bid_id}_{metadata.file_name}_p{page_number or 1}_c{chunk_idx}"
                meta_copy = metadata.model_copy()
                meta_copy.page_number = page_number
                meta_copy.is_operative_clause = is_operative_text(current_chunk)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=current_chunk,
                        metadata=meta_copy,
                        token_count=len(current_chunk) // 4,
                    )
                )
                chunk_idx += 1
                current_chunk = current_chunk[-overlap:] + f"\n\n{para}".strip()
            else:
                start = 0
                while start < len(para):
                    part = para[start : start + chunk_size]
                    chunk_id = f"{metadata.bid_id}_{metadata.file_name}_p{page_number or 1}_c{chunk_idx}"
                    meta_copy = metadata.model_copy()
                    meta_copy.page_number = page_number
                    meta_copy.is_operative_clause = is_operative_text(part)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            text=part,
                            metadata=meta_copy,
                            token_count=len(part) // 4,
                        )
                    )
                    chunk_idx += 1
                    start += chunk_size - overlap
                current_chunk = ""

    if current_chunk:
        chunk_id = f"{metadata.bid_id}_{metadata.file_name}_p{page_number or 1}_c{chunk_idx}"
        meta_copy = metadata.model_copy()
        meta_copy.page_number = page_number
        meta_copy.is_operative_clause = is_operative_text(current_chunk)
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=current_chunk,
                metadata=meta_copy,
                token_count=len(current_chunk) // 4,
            )
        )

    return chunks


class IngestionPipeline:
    """Pipeline orchestrating bid folder discovery, parsing, and chunk generation."""

    def __init__(self) -> None:
        self.html_parser = HTMLDocumentParser()
        self.pdf_parser = PDFDocumentParser()

    def ingest_bid_folder(self, folder_path: Path, bid_id: Optional[str] = None) -> List[DocumentChunk]:
        """Discover and ingest all supported documents in a bid folder dynamically."""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Bid directory not found: {folder_path}")

        detected_bid_id = bid_id or folder.name
        logger.info("Ingesting bid folder: %s (bid_id: %s)", folder, detected_bid_id)

        all_chunks: List[DocumentChunk] = []

        supported_extensions = {".pdf", ".html", ".htm"}
        files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions]
        files.sort(key=lambda f: f.name)

        for file_path in files:
            doc_type, addendum_no = classify_document(file_path.name)
            is_amendment = (doc_type == DocType.ADDENDUM)
            meta = DocumentMetadata(
                bid_id=detected_bid_id,
                file_name=file_path.name,
                doc_type=doc_type,
                addendum_number=addendum_no,
                is_amendment=is_amendment,
                hierarchy_level=2 if is_amendment else 1,
            )

            if file_path.suffix.lower() in {".html", ".htm"}:
                chunks = self.html_parser.parse(file_path, meta)
            else:
                chunks = self.pdf_parser.parse(file_path, meta)

            logger.info("Extracted %d chunks from %s (%s)", len(chunks), file_path.name, doc_type.value)
            all_chunks.extend(chunks)

        logger.info("Total %d chunks created for bid %s", len(all_chunks), detected_bid_id)
        return all_chunks
