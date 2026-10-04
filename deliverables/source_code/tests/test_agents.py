"""Unit tests for the multi-agent system (specialists, validator, reconciler, graph)."""

import sys
import unittest
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.agents.graph import agent_graph
from rfp_intelligence.agents.reconciliation import AddendumReconciliationAgent
from rfp_intelligence.agents.validator import ValidatorAgent
from rfp_intelligence.models.domain import ExtractedField, SourceCitation


class TestAgents(unittest.TestCase):
    """Test suite for multi-agent roles and LangGraph orchestration."""

    def test_validator_with_citations(self) -> None:
        validator = ValidatorAgent()
        fields = {
            "Due Date": ExtractedField(
                value="2024-07-09 14:00 CST",
                sources=[SourceCitation(file="Addendum 2.pdf", page=1)],
                confidence=0.95,
            ),
            "Bid Bond Requirement": ExtractedField(
                value=None,
                sources=[],
                confidence=0.90,
                notes="Not found in documents",
            ),
        }
        summary, failed = validator.validate_fields(fields)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.not_found, 1)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(len(failed), 0)

    def test_validator_rejects_missing_citations(self) -> None:
        validator = ValidatorAgent()
        fields = {
            "Model_no": ExtractedField(
                value="Dell Latitude 3440",
                sources=[],  # Violates grounding guardrail
                confidence=0.90,
            ),
        }
        summary, failed = validator.validate_fields(fields)
        self.assertEqual(summary.failed, 1)
        self.assertIn("Model_no", failed)

    def test_addendum_reconciliation_override(self) -> None:
        reconciler = AddendumReconciliationAgent()
        draft = {
            "Due Date": ExtractedField(
                value="June 25, 2024",
                sources=[SourceCitation(file="RFP.pdf", page=1)],
                confidence=0.8,
            )
        }
        evidence = [
            {
                "text": "Addendum 2: The proposal submission deadline is hereby extended to July 9, 2024 at 2:00 PM CST.",
                "metadata": {
                    "file_name": "Addendum 2 RFP.pdf",
                    "doc_type": "addendum",
                    "page_number": 1,
                    "addendum_number": 2,
                },
            }
        ]
        updated, changes = reconciler.reconcile(draft, evidence)
        self.assertIn("July 9, 2024", str(updated["Due Date"].value))
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].field_name, "Due Date")

    def test_graph_compiled_structure(self) -> None:
        # Verify compiled LangGraph nodes
        self.assertIsNotNone(agent_graph)
        node_names = set(agent_graph.nodes.keys())
        expected = {"planner", "retriever", "extractor", "reconciler", "validator", "retry_prep", "reporter"}
        self.assertTrue(expected.issubset(node_names))


if __name__ == "__main__":
    unittest.main()
