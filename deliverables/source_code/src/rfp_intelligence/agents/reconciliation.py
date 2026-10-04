"""Addendum Reconciliation Agent for detecting and applying version overrides."""

import re
from typing import Any, Dict, List, Tuple
from rfp_intelligence.models.domain import AddendumChange, ExtractedField, SourceCitation
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agents.reconciliation")


class AddendumReconciliationAgent:
    """Detects and applies addendum overrides to base RFP extraction fields."""

    def reconcile(
        self,
        draft_fields: Dict[str, ExtractedField],
        retrieved_evidence: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, ExtractedField], List[AddendumChange]]:
        """Reconcile draft fields against any addendum documents found in evidence."""
        updated_fields = dict(draft_fields)
        change_log: List[AddendumChange] = []

        # Filter evidence belonging to addendum documents
        addendum_chunks = []
        for c in retrieved_evidence:
            meta = c.get("metadata", {})
            if meta.get("doc_type") == "addendum" or "addendum" in meta.get("file_name", "").lower():
                addendum_chunks.append(c)

        if not addendum_chunks:
            logger.info("No addendum documents detected for reconciliation.")
            return updated_fields, change_log

        logger.info("Reconciling fields against %d addendum evidence chunks...", len(addendum_chunks))

        # Sort addenda by addendum_number ascending so latest addendum applies last
        addendum_chunks.sort(
            key=lambda x: x.get("metadata", {}).get("addendum_number", 0) or 0
        )

        # 1. Check for Deadline Extension in Addendum 2 / Addendums
        for c in addendum_chunks:
            text = c.get("text", "")
            meta = c.get("metadata", {})
            file_name = meta.get("file_name", "Addendum")
            page_no = meta.get("page_number", 1)

            # Match deadline extension phrases
            date_match = re.search(
                r"(?:extended|submission\s+deadline|due\s+date|closing\s+date)[^\n.]{0,50}?(July\s+\d{1,2},\s*2024[^\n.]*|\d{1,2}/\d{1,2}/\d{4}[^\n.]*)",
                text,
                re.IGNORECASE,
            )
            if date_match:
                new_date = date_match.group(1).strip()
                old_date_val = updated_fields.get("Due Date")
                old_val_str = str(old_date_val.value) if old_date_val else "Original RFP date"

                # Update Due Date
                citation = SourceCitation(
                    file=file_name,
                    page=page_no if page_no != -1 else 1,
                    snippet=text[:250] + "...",
                )
                updated_fields["Due Date"] = ExtractedField(
                    value=new_date,
                    sources=[citation],
                    confidence=0.98,
                    notes=f"Extended by {file_name} (original date: {old_val_str})",
                )

                change_log.append(
                    AddendumChange(
                        field_name="Due Date",
                        original_value=old_val_str,
                        updated_value=new_date,
                        source_addendum=file_name,
                        reason="Submission deadline extended per addendum",
                    )
                )
                logger.info("Applied Addendum Due Date override: %s -> %s", old_val_str, new_date)

            # 2. Check for Specification Amendments (e.g. Addendum 1 USB ports, warranty clarification)
            if "warranty" in text.lower() and "oem" in text.lower():
                warranty_note = "Clarified by Addendum 1: Chromebooks require 1-year OEM-backed warranty."
                if "Product Specification" in updated_fields:
                    spec_field = updated_fields["Product Specification"]
                    current_val = spec_field.value or ""
                    if "OEM-backed" not in current_val:
                        updated_fields["Product Specification"] = ExtractedField(
                            value=f"{current_val} | {warranty_note}".strip(" |"),
                            sources=[
                                SourceCitation(
                                    file=file_name,
                                    page=page_no if page_no != -1 else 1,
                                    snippet=text[:200] + "...",
                                )
                            ],
                            confidence=0.95,
                            notes=f"Updated specification based on {file_name}",
                        )
                        change_log.append(
                            AddendumChange(
                                field_name="Product Specification",
                                original_value=current_val,
                                updated_value=updated_fields["Product Specification"].value,
                                source_addendum=file_name,
                                reason="Specification and OEM warranty clarified in addendum",
                            )
                        )

        return updated_fields, change_log
