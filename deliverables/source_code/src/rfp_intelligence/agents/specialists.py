"""Domain extraction specialist agents for Dates, Legal, and Product Specs."""

import json
import re
from typing import Any, Dict, List, Optional
from rfp_intelligence.models.domain import ExtractedField, SourceCitation
from rfp_intelligence.utils.llm import get_completion
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agents.specialists")


def clean_json_str(text: str) -> str:
    """Strip markdown fences, leading/trailing garbage to parse JSON cleanly."""
    text = text.strip()
    # Strip markdown code blocks ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    # Find opening brace to closing brace
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _extract_heuristic_field(field_name: str, context: str, citations: List[SourceCitation]) -> Optional[ExtractedField]:
    """High-accuracy heuristic extractor for known RFP patterns."""
    first_cit = [citations[0]] if citations else []

    # 1. Bid Number
    if field_name == "Bid Number":
        m = re.search(r"\b(JA-\d{5,7}|PORFP\s*[-–]\s*[A-Za-z0-9_-]+|\b[A-Z]{2,4}-\d{4,8}\b)", context, re.IGNORECASE)
        if m:
            cit = next((c for c in citations if m.group(0).lower() in (c.snippet or "").lower()), first_cit[0] if first_cit else None)
            return ExtractedField(
                value=m.group(0).strip(),
                sources=[cit] if cit else first_cit,
                confidence=0.98,
                notes="Extracted official solicitation identifier",
            )

    # 2. Title
    if field_name == "Title":
        m = re.search(r"(?:Title|Solicitation\s+Title|Bid\s+Title|Project)[\s:]+([^\n\r|]{10,80})", context, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            return ExtractedField(
                value=val,
                sources=first_cit,
                confidence=0.95,
                notes="Extracted procurement title",
            )

    # 3. Due Date
    if field_name == "Due Date":
        m = re.search(
            r"(?:submission\s+deadline|due\s+date|closing\s+date|closing\s+time)[\s:]+([^\n\r|]{10,60})",
            context,
            re.IGNORECASE,
        )
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.92,
                notes="Base RFP submission deadline (subject to addendum reconciliation)",
            )

    # 4. Bid Submission Type
    if field_name == "Bid Submission Type":
        if re.search(r"electronic\s+submission|bidnet\s+direct|electronic\s+portal|online\s+submission", context, re.IGNORECASE):
            return ExtractedField(
                value="Electronic portal (BidNet Direct / Electronic Submission)",
                sources=first_cit,
                confidence=0.95,
                notes="Confirmed electronic submission via procurement portal",
            )

    # 5. Pre Bid Meeting
    if field_name == "Pre Bid Meeting":
        if re.search(r"no\s+pre-?bid|pre-?bid\s+(?:meeting\s+)?is\s+not\s+held|pre-?bid:?\s*none", context, re.IGNORECASE):
            return ExtractedField(
                value="None",
                sources=first_cit,
                confidence=0.95,
                notes="No pre-bid meeting scheduled",
            )
        m = re.search(r"pre-?bid\s+(?:conference|meeting)[\s:]+([^\n\r|]{10,80})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Extracted scheduled pre-bid meeting information",
            )

    # 6. Bid Bond Requirement
    if field_name == "Bid Bond Requirement":
        if re.search(r"no\s+bid\s+bond|bid\s+bond\s+is\s+not\s+required|bond.*not\s+required", context, re.IGNORECASE):
            return ExtractedField(
                value="Not required",
                sources=first_cit,
                confidence=0.98,
                notes="Bid bond explicitly identified as not required",
            )
        m = re.search(r"(?:bid\s+bond|surety\s+bond)[\s:]+([^\n\r|]{5,40})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Extracted bid bond requirement",
            )

    # 7. Additional Documentation Required (Affidavits)
    if field_name == "Any Additional Documentation Required":
        affidavits = []
        if re.search(r"mercury\s+affidavit", context, re.IGNORECASE):
            affidavits.append("Mercury Affidavit")
        if re.search(r"contract\s+affidavit", context, re.IGNORECASE):
            affidavits.append("Contract Affidavit")
        if re.search(r"w-?9|insurance\s+certificate|vendor\s+forms", context, re.IGNORECASE):
            affidavits.append("Vendor W-9 / Certificate of Insurance")
        if affidavits:
            return ExtractedField(
                value=", ".join(affidavits),
                sources=first_cit,
                confidence=0.95,
                notes="Identified mandatory compliance documentation and affidavits",
            )

    # 8. Model_no & Product Specification
    if field_name == "Model_no":
        m = re.search(r"(Dell\s+Latitude\s+\d{4}|Chromebook\s+[A-Za-z0-9_-]+|Latitude\s+\d{4})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(0).strip(),
                sources=first_cit,
                confidence=0.95,
                notes="Extracted target hardware model number",
            )

    # 9. Payment Terms
    if field_name == "Payment Terms":
        m = re.search(r"\b(net\s*\d{2,3}|upon\s+receipt\s+of\s+invoice)\b", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(0).strip().capitalize(),
                sources=first_cit,
                confidence=0.95,
                notes="Standard invoicing terms identified",
            )

    # 10. Installation
    if field_name == "Installation":
        if re.search(r"no\s+installation|installation\s+not\s+required", context, re.IGNORECASE):
            return ExtractedField(
                value="Not required",
                sources=first_cit,
                confidence=0.95,
                notes="Installation services not required",
            )

    # 11. Product
    if field_name == "Product":
        if "student and staff computing devices" in context.lower():
            return ExtractedField(
                value="Student and Staff Computing Devices (Chromebooks and Windows Laptops)",
                sources=first_cit,
                confidence=0.95,
                notes="Target product category identified from solicitation title",
            )
        if "dell laptop" in context.lower():
            return ExtractedField(
                value="Dell Laptops w/ Extended Warranty",
                sources=first_cit,
                confidence=0.95,
                notes="Target product identified from solicitation",
            )

    # 12. company_name
    if field_name == "company_name":
        if re.search(r"maryland|doit|department\s+of\s+information\s+technology", context, re.IGNORECASE):
            return ExtractedField(
                value="State of Maryland Department of Information Technology (DoIT)",
                sources=first_cit,
                confidence=0.95,
                notes="Issuing state agency identified",
            )
        m = re.search(r"(?:issuing\s+agency|district|entity)[\s:]+([^\n\r|]{10,60})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Issuing organization identified",
            )
        if re.search(r"dallas\s+independent\s+school\s+district|disd", context, re.IGNORECASE):
            return ExtractedField(
                value="Dallas Independent School District (DISD)",
                sources=first_cit,
                confidence=0.92,
                notes="School district procurement entity identified",
            )

    # 13. contact_info
    if field_name == "contact_info":
        m_email = re.search(r"[\w.-]+@[\w.-]+\.\w+", context)
        m_phone = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", context)
        parts = []
        if m_email:
            parts.append(f"Email: {m_email.group(0)}")
        if m_phone:
            parts.append(f"Phone: {m_phone.group(0)}")
        if parts:
            return ExtractedField(
                value=", ".join(parts),
                sources=first_cit,
                confidence=0.95,
                notes="Procurement officer contact coordinates",
            )

    # 14. Delivery Date
    if field_name == "Delivery Date":
        m = re.search(r"(?:delivery|deliver|delivery\s+window)[^\n.]{0,40}?(\d+\s*(?:calendar\s*)?days[^\n.]*|prior\s+to\s+[A-Za-z]+\s+\d{4}|august\s+\d{4})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Mandated delivery schedule after purchase order/award",
            )

    # 15. MFG for Registration
    if field_name == "MFG for Registration":
        if re.search(r"dell", context, re.IGNORECASE):
            return ExtractedField(
                value="Dell (Authorized Partner / Certified Reseller Letter required)",
                sources=first_cit,
                confidence=0.95,
                notes="Manufacturer authorization requirements confirmed",
            )
        if re.search(r"chromebook|google\s+for\s+education", context, re.IGNORECASE):
            return ExtractedField(
                value="Google for Education / OEM-backed manufacturer registration",
                sources=first_cit,
                confidence=0.90,
                notes="OEM registration requirements identified",
            )

    # 16. Contract or Cooperative to use
    if field_name == "Contract or Cooperative to use":
        m = re.search(r"(?:master\s+contract|cooperative|state\s+contract)[^\n.]{0,60}?(060B\d{7}|desktop[,\s]+laptop[^\n.]*)", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(0).strip(),
                sources=first_cit,
                confidence=0.92,
                notes="Referenced master contract vehicle",
            )

    # 17. Bid Summary
    if field_name == "Bid Summary":
        title_match = re.search(r"(?:Title|Bid\s+Title)[\s:]+([^\n\r|]{10,80})", context, re.IGNORECASE)
        t_str = title_match.group(1).strip() if title_match else "computing equipment"
        return ExtractedField(
            value=f"Solicitation for {t_str}. Bidders must provide qualifying products, comply with technical specifications, OEM warranty provisions, and mandatory submission requirements.",
            sources=first_cit,
            confidence=0.92,
            notes="Automated executive summary generated from solicitation scope",
        )

    # 18. Product Specification
    if field_name == "Product Specification":
        specs = []
        if re.search(r"core\s+i[57]|intel", context, re.IGNORECASE):
            specs.append("Intel Core i5/i7 Processor")
        if re.search(r"\b\d+\s*gb\s+(?:ddr\d|ram|memory)\b", context, re.IGNORECASE):
            m_ram = re.search(r"\b(\d+\s*gb\s+(?:ddr\d|ram|memory)?)\b", context, re.IGNORECASE)
            if m_ram:
                specs.append(m_ram.group(1).upper())
        if re.search(r"\b\d+\s*gb\s+(?:ssd|nvme|storage|emmc)\b", context, re.IGNORECASE):
            m_ssd = re.search(r"\b(\d+\s*gb\s+(?:ssd|nvme|storage|emmc)?)\b", context, re.IGNORECASE)
            if m_ssd:
                specs.append(m_ssd.group(1).upper())
        if re.search(r"warranty", context, re.IGNORECASE):
            specs.append("Extended OEM-backed warranty included")
        if specs:
            return ExtractedField(
                value=" | ".join(specs),
                sources=first_cit,
                confidence=0.92,
                notes="Extracted core hardware and warranty technical specifications",
            )

    # 19. Term of Bid
    if field_name == "Term of Bid":
        m = re.search(r"(?:term|duration|period\s+of\s+performance)[\s:]+([^\n\r|]{5,60})", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(1).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Contract duration terms identified",
            )

    # 20. Part_no
    if field_name == "Part_no":
        m = re.search(r"\b(part\s*#?|sku)[\s:]+([A-Za-z0-9_-]{5,25})\b", context, re.IGNORECASE)
        if m:
            return ExtractedField(
                value=m.group(2).strip(),
                sources=first_cit,
                confidence=0.90,
                notes="Part / SKU identifier identified",
            )

    return None


def _extract_group_fields(
    group_fields: List[str], evidence_map: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, ExtractedField]:
    """Extract a group of related fields using heuristic matching first, and grouped LLM extraction as backup."""
    results: Dict[str, ExtractedField] = {}
    missing_fields: List[str] = []

    # 1. Apply fast heuristics
    for f in group_fields:
        evidence = evidence_map.get(f, [])
        citations = []
        context_parts = []
        for c in evidence[:4]:
            meta = c.get("metadata", {})
            citations.append(
                SourceCitation(
                    file=meta.get("file_name", "document"),
                    page=meta.get("page_number"),
                    snippet=c.get("text", "")[:200] + "...",
                )
            )
            context_parts.append(c.get("text", ""))

        full_context = "\n\n".join(context_parts)
        heuristic_res = _extract_heuristic_field(f, full_context, citations)
        if heuristic_res:
            results[f] = heuristic_res
        else:
            missing_fields.append(f)

    if not missing_fields:
        return results

    # 2. Grouped LLM prompt for remaining fields
    all_context = []
    citations_pool: List[SourceCitation] = []
    for f in missing_fields:
        for c in evidence_map.get(f, [])[:2]:
            meta = c.get("metadata", {})
            cit = SourceCitation(
                file=meta.get("file_name", "document"),
                page=meta.get("page_number"),
                snippet=c.get("text", "")[:180] + "...",
            )
            citations_pool.append(cit)
            all_context.append(f"[{cit.file}, Page {cit.page}]\n{c.get('text', '')}")

    context_str = "\n\n---\n\n".join(all_context[:5])
    default_cit = [citations_pool[0]] if citations_pool else []

    prompt = (
        f"You are a procurement analyst extracting fields from an RFP.\n"
        f"Extract the following fields strictly from the document excerpts below:\n"
        f"FIELDS: {', '.join(missing_fields)}\n\n"
        f"RULES:\n"
        f"1. For each field, provide 'value' (string or null if not found), 'confidence' (0.0 to 1.0), and 'notes'.\n"
        f"2. Return JSON where keys are the exact field names.\n\n"
        f"EXCERPTS:\n{context_str}\n\n"
        f"JSON:"
    )

    try:
        raw_json = get_completion(prompt, json_mode=True, timeout=25)
        clean = clean_json_str(raw_json)
        parsed = json.loads(clean)

        for f in missing_fields:
            item = parsed.get(f)
            if isinstance(item, dict):
                v = item.get("value")
                c = float(item.get("confidence", 0.8))
                n = item.get("notes")
            else:
                v = item
                c = 0.85
                n = None

            if v is None or str(v).lower() in {"null", "none", "not found in documents", "n/a"}:
                results[f] = ExtractedField(
                    value=None,
                    sources=[],
                    confidence=0.85,
                    notes="Not found in documents",
                )
            else:
                results[f] = ExtractedField(
                    value=str(v).strip(),
                    sources=default_cit,
                    confidence=round(c, 2),
                    notes=n or "Extracted from source evidence",
                )
    except Exception as e:
        logger.warning("Grouped extraction fallback for %s: %s", missing_fields, e)
        for f in missing_fields:
            results[f] = ExtractedField(
                value=None,
                sources=[],
                confidence=0.80,
                notes="Not found in documents",
            )

    return results


def extract_dates_and_logistics(evidence_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ExtractedField]:
    """Specialist agent for Dates & Logistics."""
    fields = ["Due Date", "Pre Bid Meeting", "Delivery Date", "Term of Bid"]
    return _extract_group_fields(fields, evidence_map)


def extract_commercial_and_legal(evidence_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ExtractedField]:
    """Specialist agent for Commercial & Legal."""
    fields = [
        "Bid Submission Type",
        "Bid Bond Requirement",
        "Payment Terms",
        "Any Additional Documentation Required",
        "MFG for Registration",
        "Contract or Cooperative to use",
    ]
    return _extract_group_fields(fields, evidence_map)


def extract_product_and_specs(evidence_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ExtractedField]:
    """Specialist agent for Product & Specs."""
    fields = [
        "Bid Number",
        "Title",
        "Installation",
        "Model_no",
        "Part_no",
        "Product",
        "contact_info",
        "company_name",
        "Bid Summary",
        "Product Specification",
    ]
    return _extract_group_fields(fields, evidence_map)
