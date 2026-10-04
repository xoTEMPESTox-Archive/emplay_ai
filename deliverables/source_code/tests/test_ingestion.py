"""Unit tests for document parsing, metadata classification, and chunking."""

import sys
import unittest
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.ingestion.parser import (
    clean_text,
    classify_document,
    chunk_text,
    IngestionPipeline,
)
from rfp_intelligence.models.domain import DocType, DocumentMetadata
from rfp_intelligence.config import REPO_ROOT


class TestIngestion(unittest.TestCase):
    """Test suite for ingestion and parser components."""

    def test_clean_text(self) -> None:
        raw = "This is a com-\nputing device. \t\tMultiple   spaces  and\n\n\n\nextra lines."
        cleaned = clean_text(raw)
        self.assertIn("computing device.", cleaned)
        self.assertNotIn("com-", cleaned)
        self.assertNotIn("\t\t", cleaned)

    def test_classify_document(self) -> None:
        doc_type, num = classify_document("Addendum 2 RFP JA-207652.pdf")
        self.assertEqual(doc_type, DocType.ADDENDUM)
        self.assertEqual(num, 2)

        doc_type, num = classify_document("Bid Information - BidNet Direct.html")
        self.assertEqual(doc_type, DocType.BID_PAGE)
        self.assertIsNone(num)

        doc_type, num = classify_document("Dell_Laptop_Specs.pdf")
        self.assertEqual(doc_type, DocType.SPECS)

        doc_type, num = classify_document("Contract_Affidavit.pdf")
        self.assertEqual(doc_type, DocType.AFFIDAVIT)

        doc_type, num = classify_document("PORFP_-_Dell_Laptop_Final.pdf")
        self.assertEqual(doc_type, DocType.RFP)

    def test_chunk_text(self) -> None:
        meta = DocumentMetadata(bid_id="TestBid", file_name="sample.pdf", doc_type=DocType.RFP)
        text = "Paragraph one with details.\n\nParagraph two with more specifications."
        chunks = chunk_text(text, meta, page_number=1, chunk_size=200, overlap=50)
        self.assertGreaterEqual(len(chunks), 1)
        self.assertIn("TestBid", chunks[0].chunk_id)
        self.assertEqual(chunks[0].metadata.page_number, 1)

    def test_ingest_bid2_folder(self) -> None:
        bid2_path = REPO_ROOT / "Assignment-Data-Statements (AI Engineer-Emplay Inc)" / "Bid2"
        if not bid2_path.exists():
            self.skipTest("Bid2 directory not found")

        pipeline = IngestionPipeline()
        chunks = pipeline.ingest_bid_folder(bid2_path, bid_id="Bid2")
        self.assertGreater(len(chunks), 5)
        # Ensure metadata is populated across chunks
        doc_types = {c.metadata.doc_type for c in chunks}
        self.assertIn(DocType.BID_PAGE, doc_types)
        self.assertIn(DocType.SPECS, doc_types)


if __name__ == "__main__":
    unittest.main()
