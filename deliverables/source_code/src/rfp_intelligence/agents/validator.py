"""Validator and Critic Agent verifying citation grounding, formats, and hallucination guardrails."""

from typing import Dict, List, Tuple
from rfp_intelligence.models.domain import ExtractedField, ValidationSummary
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agents.validator")


class ValidatorAgent:
    """Critic agent validating field groundedness, schema formatting, and hallucinations."""

    def validate_fields(
        self,
        fields: Dict[str, ExtractedField],
    ) -> Tuple[ValidationSummary, List[str]]:
        """Validate all extracted fields and return a ValidationSummary and list of failed field names.

        Args:
            fields: Map of field name to ExtractedField instance.

        Returns:
            Tuple of (ValidationSummary, failed_field_names).
        """
        passed = 0
        failed = 0
        not_found = 0
        issues: List[str] = []
        failed_fields: List[str] = []

        for field_name, field in fields.items():
            # Check 1: Null values / Not found in documents
            if field.value is None or str(field.value).lower() in {"null", "none", "not found in documents"}:
                not_found += 1
                # If notes doesn't acknowledge absence, add note
                if not field.notes:
                    field.notes = "Not found in documents"
                continue

            val_str = str(field.value).strip()

            # Check 2: Citation Grounding Guardrail
            # Every extracted non-null value MUST have at least one source citation
            if not field.sources:
                failed += 1
                issue = f"Field '{field_name}' has non-null value '{val_str}' but zero source citations."
                issues.append(issue)
                failed_fields.append(field_name)
                logger.warning("Validation rejected: %s", issue)
                continue

            # Check 3: Format & Reasonable Length Sanity Check
            if len(val_str) < 1:
                failed += 1
                issues.append(f"Field '{field_name}' contains empty string value.")
                failed_fields.append(field_name)
                continue

            # Check 4: Hallucination phrase check
            hallucination_indicators = [
                "i think",
                "presumably",
                "as an ai",
                "language model",
                "cannot verify",
            ]
            if any(ind in val_str.lower() for ind in hallucination_indicators):
                failed += 1
                issue = f"Field '{field_name}' contains speculative or hallucinated language: '{val_str}'"
                issues.append(issue)
                failed_fields.append(field_name)
                continue

            # Passed validation
            passed += 1

        summary = ValidationSummary(
            passed=passed,
            failed=failed,
            not_found=not_found,
            issues=issues,
        )
        logger.info(
            "Validation completed: %d passed, %d failed, %d not found",
            passed,
            failed,
            not_found,
        )
        return summary, failed_fields
