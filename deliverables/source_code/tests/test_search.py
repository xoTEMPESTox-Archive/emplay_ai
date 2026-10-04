"""Unit tests for the Hybrid Search Engine (Vector + BM25 + RRF)."""

import shutil
import sys
import unittest
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.models.domain import (
    DocType,
    DocumentChunk,
    DocumentMetadata,
    SearchQuery,
)
from rfp_intelligence.search.engine import HybridSearchEngine, tokenize_for_bm25


class TestSearchEngine(unittest.TestCase):
    """Test suite for hybrid retrieval and indexing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_db_dir = Path(__file__).resolve().parent / "test_chroma_tmp"
        cls.engine = HybridSearchEngine(persist_dir=cls.test_db_dir)

        # Create sample test chunks
        cls.meta1 = DocumentMetadata(
            bid_id="Bid1",
            file_name="rfp_doc.pdf",
            doc_type=DocType.RFP,
            page_number=3,
        )
        cls.chunk1 = DocumentChunk(
            chunk_id="c1",
            text="The submission deadline for proposals is July 9, 2024 at 2:00 PM CST.",
            metadata=cls.meta1,
        )

        cls.meta2 = DocumentMetadata(
            bid_id="Bid2",
            file_name="dell_specs.pdf",
            doc_type=DocType.SPECS,
            page_number=1,
        )
        cls.chunk2 = DocumentChunk(
            chunk_id="c2",
            text="Dell Latitude 3440 Laptop with Intel Core i5, 16GB RAM and 512GB SSD.",
            metadata=cls.meta2,
        )

        cls.engine.index_chunks([cls.chunk1, cls.chunk2])

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.test_db_dir.exists():
            try:
                shutil.rmtree(cls.test_db_dir)
            except Exception:
                pass

    def test_tokenization(self) -> None:
        tokens = tokenize_for_bm25("Dell Latitude-3440 Laptop!")
        self.assertIn("dell", tokens)
        self.assertIn("latitude", tokens)
        self.assertIn("3440", tokens)

    def test_hybrid_search_deadline(self) -> None:
        query = SearchQuery(q="submission deadline July 2024", top_k=2)
        results = self.engine.search(query)
        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertIn("deadline", top.text.lower())
        self.assertIsNotNone(top.citation.page)
        self.assertEqual(top.citation.file, "rfp_doc.pdf")

    def test_metadata_filtering(self) -> None:
        # Search specifically for Bid2
        query = SearchQuery(q="laptop specs", bid_id="Bid2", top_k=2)
        results = self.engine.search(query)
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertEqual(r.metadata.bid_id, "Bid2")

    def test_bid_catalog_and_decomposition(self) -> None:
        from rfp_intelligence.search.decomposition import decompose_query, detect_bids_rule_based
        
        # Test rule-based comparative detection
        bids, is_comp = detect_bids_rule_based("What are the specs for Bid1 vs Bid2?")
        self.assertTrue(is_comp)
        self.assertIn("Bid1", bids)
        self.assertIn("Bid2", bids)

        # Test catalog generation
        catalog = self.engine.get_bid_catalog()
        self.assertIn("Bid1", catalog)
        self.assertIn("Bid2", catalog)

        # Test decomposition fallback
        decomposed = decompose_query("Compare the warranty requirements of both bids.", catalog=catalog)
        self.assertTrue(decomposed.is_comparative)
        self.assertIn("Bid1", decomposed.target_bids)
        self.assertIn("Bid2", decomposed.target_bids)


if __name__ == "__main__":
    unittest.main()
