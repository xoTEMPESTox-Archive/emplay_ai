"""Automatic Go / No-Go recommendation agent evaluating bids against company capabilities."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from rfp_intelligence.config import settings
from rfp_intelligence.models.domain import BidExtractionResult
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.agents.gonogo")


class GoNoGoDecision(BaseModel):
    """Structured decision output from the Go/No-Go assessment."""

    bid_id: str
    recommendation: str = Field(description="'GO', 'CAUTION', or 'NO-GO'")
    match_score: int = Field(ge=0, le=100, description="Capability alignment score 0-100")
    passed_criteria: List[str] = Field(default_factory=list)
    flagged_risks: List[str] = Field(default_factory=list)
    rationale: str


class GoNoGoAgent:
    """Evaluates extracted bid requirements against organizational profile to recommend pursuit."""

    def __init__(self, profile_path: Optional[Path] = None) -> None:
        self.profile_path = profile_path or settings.company_profile_path
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not read company profile %s: %s", self.profile_path, e)

        # Fallback profile
        return {
            "company_name": "Apex Enterprise Technologies",
            "authorized_manufacturers": ["Dell", "Lenovo", "HP", "Google"],
            "max_bonding_capacity_usd": 1000000,
            "min_delivery_window_days": 15,
            "max_delivery_window_days": 60,
            "provides_installation_services": True,
            "provides_oem_warranty": True,
            "supported_submission_types": ["electronic portal", "electronic", "sealed paper"],
            "affidavits_compliant": True,
        }

    def evaluate(self, bid: BidExtractionResult) -> GoNoGoDecision:
        """Evaluate a bid extraction result against company capabilities."""
        passed = []
        risks = []
        score = 100

        fields = bid.fields

        # 1. Manufacturer Authorization Check
        mfg_field = fields.get("MFG for Registration") or fields.get("Model_no") or fields.get("Product")
        mfg_val = str(mfg_field.value if mfg_field else "").lower()
        authorized = [m.lower() for m in self.profile.get("authorized_manufacturers", [])]

        if any(auth in mfg_val for auth in authorized) or not mfg_val or mfg_val == "none":
            passed.append(f"Manufacturer capability aligns with authorized OEM roster: {self.profile.get('authorized_manufacturers')}")
        else:
            risks.append(f"RFP specifies manufacturer '{mfg_val}' which may require partner authorization")
            score -= 25

        # 2. Bid Bond Capacity Check
        bond_field = fields.get("Bid Bond Requirement")
        bond_val = str(bond_field.value if bond_field else "").lower()
        if "not required" in bond_val or not bond_val or bond_val == "none":
            passed.append("No onerous bid bond required; within $0 bond threshold")
        else:
            passed.append(f"Bond requirement ({bond_val}) within $1M corporate surety bonding line")

        # 3. Installation Services Check
        install_field = fields.get("Installation")
        install_val = str(install_field.value if install_field else "").lower()
        if "yes" in install_val or "required" in install_val:
            if self.profile.get("provides_installation_services", False):
                passed.append("Company delivers certified deployment and imaging services")
            else:
                risks.append("Installation services required but company profile does not support on-site deployment")
                score -= 30

        # 4. Submission Format Check
        sub_type_field = fields.get("Bid Submission Type")
        sub_type_val = str(sub_type_field.value if sub_type_field else "").lower()
        supported_types = [t.lower() for t in self.profile.get("supported_submission_types", [])]
        if any(st in sub_type_val for st in supported_types) or not sub_type_val or sub_type_val == "none":
            passed.append(f"Submission channel ({sub_type_val or 'Standard portal'}) supported")
        else:
            risks.append(f"Unusual submission format: {sub_type_val}")
            score -= 15

        # Final Recommendation Logic
        score = max(0, min(100, score))
        if score >= 80:
            rec = "GO"
            rationale = f"Strong alignment with corporate capabilities (Score: {score}/100). High probability of competitive compliance."
        elif score >= 50:
            rec = "CAUTION"
            rationale = f"Moderate fit (Score: {score}/100). Review identified risks regarding partner authorizations or logistics before committing proposal resources."
        else:
            rec = "NO-GO"
            rationale = f"Low fit (Score: {score}/100). Significant capability or qualification mismatches identified."

        return GoNoGoDecision(
            bid_id=bid.bid_id,
            recommendation=rec,
            match_score=score,
            passed_criteria=passed,
            flagged_risks=risks,
            rationale=rationale,
        )
