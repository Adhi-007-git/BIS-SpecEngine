"""
Compliance Engine: Analyzes regulatory and conformity requirements
including BIS Product Certification (ISI Mark), Compulsory Registration Scheme (CRS),
Quality Control Orders (QCOs), and Public Procurement orders.
Strictly returns 'Verification required' when authoritative data is absent.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ComplianceEngine:
    """Evaluates mandatory quality control orders and conformity assessment schemes."""

    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, List[Dict[str, Any]]]:
        registry_path = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "qco_registry.json"
        if not registry_path.exists():
            logger.warning(f"QCO Registry file missing at {registry_path}")
            return {}
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    logger.error("QCO Registry must be a JSON object (dict).")
                    return {}
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Malformed QCO Registry JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading QCO Registry: {e}")
            return {}

    def evaluate_compliance(self, standard_number: str, scope_text: str = "") -> List[Dict[str, Any]]:
        """Evaluates whether an identified standard has a known mandatory QCO or certification.
        If authoritative data is not verified in the registry, returns 'Verification required'."""
        cleaned_std = standard_number.split(":")[0].strip()

        # Exact matching against known registry keys (e.g. 'IS 694', 'IS 1554 (Part 1)')
        for key, requirements in self.registry.items():
            if cleaned_std == key.strip():
                return requirements

        # Default rule: Never invent regulatory requirements
        return [
            {
                "scheme": "Conformity Assessment Verification",
                "mark": "Verification required",
                "authority": "Bureau of Indian Standards (BIS)",
                "mandate": "No verified mandatory Quality Control Order (QCO) on record in active registry. Verification required.",
                "status": "Verification required",
                "evidence_ref": "Live BIS portal or GeM regulatory database check recommended"
            }
        ]
