"""Test configuration module initialization and defaults."""

import sys
import unittest
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.config import Settings


class TestConfig(unittest.TestCase):
    """Test suite for Settings configuration."""

    def test_default_settings(self) -> None:
        """Verify default configuration loads with expected defaults."""
        settings = Settings()
        self.assertTrue(bool(settings.llm_model))
        self.assertTrue(bool(settings.embedding_model))
        self.assertEqual(settings.top_k_retrieval, 5)
        self.assertIsInstance(settings.vector_db_dir, Path)


if __name__ == "__main__":
    unittest.main()
