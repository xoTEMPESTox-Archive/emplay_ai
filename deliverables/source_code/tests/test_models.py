"""Test core domain and Pydantic models serialization and validation."""

import json
import sys
import unittest
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.models.domain import (
    DocType,
    DocumentMetadata,
    ExtractedField,
    SourceCitation,
    BidExtractionResult,
    ValidationSummary,
    REQUIRED_RFP_FIELDS,
)


class TestModels(unittest.TestCase):
    """Test suite for domain models."""

    def test_required_fields_count(self) -> None:
        """Verify that exactly 20 mandatory fields are defined per assignment."""
        self.assertEqual(len(REQUIRED_RFP_FIELDS), 20)
        self.assertIn("Bid Number", REQUIRED_RFP_FIELDS)
        self.assertIn("Due Date", REQUIRED_RFP_FIELDS)
        self.assertIn("Bid Bond Requirement", REQUIRED_RFP_FIELDS)

    def test_document_metadata_defaults(self) -> None:
        """Verify document metadata defaults and enumeration."""
        meta = DocumentMetadata(bid_id="Bid1", file_name="sample.pdf", doc_type=DocType.RFP)
        self.assertEqual(meta.bid_id, "Bid1")
        self.assertEqual(meta.doc_type, DocType.RFP)
        self.assertIsNone(meta.page_number)

    def test_bid_extraction_result_json_schema(self) -> None:
        """Verify BidExtractionResult matches assignment section 8.1 structure."""
        citation = SourceCitation(file="Addendum 2.pdf", page=1, snippet="Extended to Friday")
        field = ExtractedField(
            value="2026-10-15 14:00 EST",
            sources=[citation],
            confidence=0.95,
            notes="Extended by Addendum 2",
        )
        not_found_field = ExtractedField(
            value=None,
            sources=[],
            confidence=0.80,
            notes="Not found in documents",
        )

        result = BidExtractionResult(
            bid_id="Bid1",
            fields={
                "Due Date": field,
                "Bid Bond Requirement": not_found_field,
            },
            validation=ValidationSummary(passed=1, failed=0, not_found=1),
        )

        data = result.model_dump()
        self.assertEqual(data["bid_id"], "Bid1")
        self.assertEqual(data["fields"]["Due Date"]["value"], "2026-10-15 14:00 EST")
        self.assertEqual(data["fields"]["Due Date"]["sources"][0]["file"], "Addendum 2.pdf")
        self.assertIsNone(data["fields"]["Bid Bond Requirement"]["value"])
        self.assertEqual(data["validation"]["passed"], 1)

        # Ensure JSON serializable
        json_str = json.dumps(data)
        self.assertIn("Addendum 2.pdf", json_str)


if __name__ == "__main__":
    unittest.main()
