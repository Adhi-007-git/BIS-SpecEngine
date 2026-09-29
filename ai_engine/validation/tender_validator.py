"""
Tender Validator Service for SIH26108: Pre-Publish Tender Validation (Feature M10).
Performs deterministic, evidence-grounded validation of procurement specifications
against the curated Indian Standards catalogue (21 standards) and official QCO registry (5 records).

Rules Evaluated:
- Rule A: Superseded or obsolete standards detection using verified supersedes relationships.
- Rule B: Quality Control Order (QCO) and mandatory certification verification.
- Rule C: Foreign standards precedence and equivalency review (ASTM, IEC, DIN, etc.).
- Rule D: Normative references and verified test methods consistency.
- Rule E: Evidence grounding and catalogue completeness.

Advisory Decision-Support Notice:
Outputs strictly support procurement officer review. Never declares legal compliance
or authorizes automatic publishing.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
import re
import uuid
from datetime import datetime

logger = logging.getLogger("sih26108.validation")

ADVISORY_DISCLAIMER = (
    "Advisory decision-support output only. This report is not statutory legal certification, "
    "does not guarantee tender compliance, and does not authorize publication. The responsible "
    "procurement officer must independently verify applicable standards, current QCO requirements, "
    "procurement rules, and source documents before making a decision."
)

DATA_LIMITATIONS = [
    "Validation is evaluated strictly against the verified local catalogue (21 curated standards) and QCO registry (5 records).",
    "Uncatalogued standards cannot be verified automatically and require manual officer review on the BIS portal (manakonline.in).",
    "Automated checks do not assess supplier financial capability, bid eligibility, or commercial contract terms.",
    "Detection is based on textual pattern matching and verified catalogue metadata; OCR degradation or unconventional phrasing may affect extraction."
]

CHECKS_COMPLETED = [
    "Rule A: Verification of cited Indian Standards against catalogue supersedes relationships and lifecycle status.",
    "Rule B: Verification of product and standard applicability against official DPIIT/BIS Quality Control Orders.",
    "Rule C: Detection of foreign standards (ASTM, IEC, BS, DIN, ISO, IEEE, EN) for officer equivalency review.",
    "Rule D: Verification of normative references and mandatory test method citations.",
    "Rule E: Verification of evidence grounding and completeness against local catalogue records."
]

CHECKS_NOT_COMPLETED = [
    "Full statutory Make-in-India order compliance verification (requires designated procurement legal counsel).",
    "Real-time BIS Gazette notification synchronization (evaluation uses local verified dataset v1.0-real-21).",
    "Tender commercial clauses, eligibility criteria, and pricing evaluation (out of technical validation scope)."
]


class TenderValidator:
    """Deterministic validation service for pre-publish tender technical specifications."""

    IS_PATTERN = re.compile(
        r'\b(IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([A-Za-z0-9\s]+\))?(?::[0-9]{4})?)\b',
        re.IGNORECASE
    )

    FOREIGN_PATTERN = re.compile(
        r'(?<!IS\/)(?<!IS\s\/)\b((?:ASTM\s+[A-Za-z0-9\-]+)|(?:IEC\s+[0-9]+(?:\-[0-9]+)?)|(?:DIN\s+[0-9]+)|(?:BS\s+[0-9]+)|(?:IEEE\s+[0-9]+)|(?:EN\s+[0-9]+))\b',
        re.IGNORECASE
    )

    MANDATORY_CERT_PATTERN = re.compile(
        r'\b(ISI\s*Mark|BIS\s*certif\w*|BIS\s*licen\w*|QCO|Scheme\s*I\b|mandatory\s*certif\w*|compulsory\s*regist\w*|Standard\s*Mark)\b',
        re.IGNORECASE
    )

    def __init__(
        self,
        catalogue_path: Optional[Path] = None,
        qco_path: Optional[Path] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.catalogue_path = catalogue_path or (base_dir / "data" / "real" / "standards_catalogue.json")
        self.qco_path = qco_path or (base_dir / "data" / "real" / "qco_registry.json")

        self.standards_list: List[Dict[str, Any]] = []
        self.standards_by_num: Dict[str, Dict[str, Any]] = {}
        self.standards_by_base: Dict[str, List[Dict[str, Any]]] = {}
        self.supersedes_map: Dict[str, Dict[str, Any]] = {}
        self.qco_registry: Dict[str, List[Dict[str, Any]]] = {}

        self._load_catalogue()
        self._load_qco_registry()

    def _load_catalogue(self) -> None:
        if not self.catalogue_path.exists():
            logger.warning("Catalogue path not found: %s", self.catalogue_path)
            return

        try:
            with open(self.catalogue_path, "r", encoding="utf-8") as f:
                self.standards_list = json.load(f)

            for std in self.standards_list:
                std_num = std.get("standard_number", "").strip()
                if not std_num:
                    continue
                self.standards_by_num[std_num] = std

                base_code = self._extract_base_code(std_num)
                self.standards_by_base.setdefault(base_code, []).append(std)

                supersedes = std.get("supersedes")
                if supersedes:
                    clean_sup = self._normalize_is_string(supersedes)
                    self.supersedes_map[clean_sup] = std

            logger.info(
                "TenderValidator loaded %d standards and %d supersedes records.",
                len(self.standards_list),
                len(self.supersedes_map)
            )
        except Exception as e:
            logger.error("Error loading standards catalogue for TenderValidator: %s", e)

    def _load_qco_registry(self) -> None:
        if not self.qco_path.exists():
            logger.warning("QCO registry path not found: %s", self.qco_path)
            return

        try:
            with open(self.qco_path, "r", encoding="utf-8") as f:
                self.qco_registry = json.load(f)
            logger.info("TenderValidator loaded %d QCO registry items.", len(self.qco_registry))
        except Exception as e:
            logger.error("Error loading QCO registry for TenderValidator: %s", e)

    @staticmethod
    def _normalize_is_string(s: str) -> str:
        """Normalizes standard string: clean whitespace, uniform casing."""
        if not s:
            return ""
        cleaned = re.sub(r'\s+', ' ', s).strip()
        # Ensure uppercase 'IS' or 'IS/IEC'
        if cleaned.upper().startswith("IS"):
            prefix_len = 2
            if cleaned.upper().startswith("IS/IEC"):
                prefix_len = 6
                cleaned = "IS/IEC" + cleaned[prefix_len:]
            else:
                cleaned = "IS" + cleaned[prefix_len:]
        return cleaned

    @staticmethod
    def _extract_base_code(std_str: str) -> str:
        """Extracts the base standard identifier without the publication year (e.g. 'IS 456' from 'IS 456:2000')."""
        norm = re.sub(r'\s+', ' ', std_str).strip()
        return norm.split(":")[0].strip()

    @staticmethod
    def _extract_year(std_str: str) -> Optional[str]:
        """Extracts the 4-digit year from an IS standard string if present."""
        if ":" in std_str:
            parts = std_str.split(":")
            if len(parts) > 1 and re.match(r'^\d{4}$', parts[-1].strip()):
                return parts[-1].strip()
        return None

    def validate(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes pre-publish validation on tender text or document chunks.
        Returns a complete, typed validation report dictionary.
        """
        if not text or not text.strip():
            raise ValueError("Tender text cannot be empty.")

        clean_text = text.strip()
        findings: List[Dict[str, Any]] = []

        # ── Rule A: Superseded or Obsolete Standards ─────────────────────────
        rule_a_findings = self._evaluate_rule_a(clean_text, document_chunks)
        findings.extend(rule_a_findings)

        # ── Rule B: QCO and Mandatory Certification ──────────────────────────
        rule_b_findings = self._evaluate_rule_b(clean_text, document_chunks)
        findings.extend(rule_b_findings)

        # ── Rule C: Foreign Standards ────────────────────────────────────────
        rule_c_findings = self._evaluate_rule_c(clean_text, document_chunks)
        findings.extend(rule_c_findings)

        # ── Rule D: Normative References and Testing ─────────────────────────
        rule_d_findings = self._evaluate_rule_d(clean_text, document_chunks)
        findings.extend(rule_d_findings)

        # ── Rule E: Evidence and Completeness ────────────────────────────────
        rule_e_findings = self._evaluate_rule_e(clean_text, document_chunks)
        findings.extend(rule_e_findings)

        # ── Compute Summary Counts & Overall Status ───────────────────────────
        summary_counts = {
            "CRITICAL": 0,
            "WARNING": 0,
            "INFO": 0,
            "MANUAL_REVIEW_REQUIRED": 0
        }
        for f in findings:
            sev = f.get("severity", "INFO")
            if sev in summary_counts:
                summary_counts[sev] += 1
            else:
                summary_counts[sev] = 1

        if summary_counts["CRITICAL"] > 0:
            overall_status = "REQUIRES_AMENDMENT"
        elif summary_counts["WARNING"] > 0 or summary_counts["MANUAL_REVIEW_REQUIRED"] > 0:
            overall_status = "OFFICER_REVIEW_REQUIRED"
        else:
            overall_status = "NO_BLOCKING_ISSUES_DETECTED"

        validation_id = f"val_{uuid.uuid4().hex[:8]}"

        return {
            "validation_id": validation_id,
            "document_id": document_id,
            "input_source": "DOCUMENT_UPLOAD" if document_id else "DIRECT_TEXT",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "summary_counts": summary_counts,
            "overall_status": overall_status,
            "findings": findings,
            "checks_completed": CHECKS_COMPLETED,
            "checks_not_completed": CHECKS_NOT_COMPLETED,
            "data_limitations": DATA_LIMITATIONS,
            "advisory_disclaimer": ADVISORY_DISCLAIMER,
            "officer_review_status": "PENDING",
            "officer_review": None
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Rule Evaluation Implementations
    # ─────────────────────────────────────────────────────────────────────────

    def _find_clause_excerpt(
        self,
        full_text: str,
        term: str,
        document_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Optional[int]]:
        """Finds a context excerpt around the term, optionally with page information."""
        page_num: Optional[int] = None

        if document_chunks:
            for chunk in document_chunks:
                chunk_content = chunk.get("content", "")
                if term.lower() in chunk_content.lower():
                    page_num = chunk.get("page_number") or chunk.get("page")
                    # Extract surrounding sentence or 120 chars
                    pos = chunk_content.lower().find(term.lower())
                    start = max(0, pos - 40)
                    end = min(len(chunk_content), pos + len(term) + 60)
                    snippet = chunk_content[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(chunk_content):
                        snippet = snippet + "..."
                    page_label = f" (Page {page_num})" if page_num else ""
                    return f"{snippet}{page_label}", page_num

        pos = full_text.lower().find(term.lower())
        if pos != -1:
            start = max(0, pos - 40)
            end = min(len(full_text), pos + len(term) + 60)
            snippet = full_text[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(full_text):
                snippet = snippet + "..."
            return snippet, None

        return f"Specification references '{term}'", None

    def _evaluate_rule_a(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rule A — Superseded or obsolete standards:
        - Detect standard identifiers explicitly present in the tender text.
        - Compare with verified supersedes relationships and lifecycle info.
        - If confirmed superseded: CRITICAL finding citing verified replacement.
        - Do not assume edition is obsolete solely because year is old.
        - If replacement status cannot be verified: MANUAL_REVIEW_REQUIRED.
        """
        findings = []
        raw_matches = self.IS_PATTERN.findall(text)
        seen_standards = set()

        for raw_match in raw_matches:
            norm_std = self._normalize_is_string(raw_match)
            if norm_std.upper() in seen_standards:
                continue
            seen_standards.add(norm_std.upper())

            excerpt, _ = self._find_clause_excerpt(text, raw_match, document_chunks)
            year = self._extract_year(norm_std)
            base_code = self._extract_base_code(norm_std)

            # 1. Check if confirmed superseded in verified catalogue
            replacement_std = None
            for sup_key, active_rec in self.supersedes_map.items():
                if sup_key.upper() == norm_std.upper() or (
                    year and self._extract_base_code(sup_key).upper() == base_code.upper() and self._extract_year(sup_key) == year
                ):
                    replacement_std = active_rec
                    break

            if replacement_std:
                findings.append({
                    "id": f"fnd_a_{uuid.uuid4().hex[:6]}",
                    "rule_id": "RULE_A_SUPERSEDED",
                    "rule_name": "Superseded or Obsolete Standard",
                    "severity": "CRITICAL",
                    "description": (
                        f"Standard edition '{norm_std}' cited in the tender is confirmed superseded by "
                        f"active standard '{replacement_std['standard_number']}' ({replacement_std.get('title', '')})."
                    ),
                    "clause_excerpt": excerpt,
                    "standard_identifier": norm_std,
                    "recommended_action": (
                        f"Amend tender specification to cite the active replacement standard "
                        f"'{replacement_std['standard_number']}' ({replacement_std.get('edition', 'Latest Revision')})."
                    ),
                    "evidence_source": "Bureau of Indian Standards Official Catalogue",
                    "evidence_record_id": replacement_std["standard_number"],
                    "evidence_excerpt": (
                        f"Verified catalogue record for '{replacement_std['standard_number']}' explicitly states: "
                        f"supersedes '{replacement_std.get('supersedes')}'. Lifecycle status: '{replacement_std.get('status', 'Active')}'."
                    ),
                    "confidence_status": "VERIFIED_FACT"
                })
                continue

            # 2. Check if this is a verified active standard in catalogue
            active_exact = self.standards_by_num.get(norm_std)
            if not active_exact and not year:
                # Year not specified, check if base standard exists
                base_matches = self.standards_by_base.get(base_code, [])
                if base_matches:
                    active_exact = base_matches[0]

            if active_exact and active_exact.get("status") == "Active":
                if year and active_exact.get("standard_number") == norm_std:
                    # Verified active edition
                    findings.append({
                        "id": f"fnd_a_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_A_SUPERSEDED",
                        "rule_name": "Active Standard Edition Verified",
                        "severity": "INFO",
                        "description": f"Standard '{norm_std}' is verified as an active, current Indian Standard in the BIS catalogue.",
                        "clause_excerpt": excerpt,
                        "standard_identifier": norm_std,
                        "recommended_action": "No edition amendment required.",
                        "evidence_source": "Bureau of Indian Standards Official Catalogue",
                        "evidence_record_id": active_exact["standard_number"],
                        "evidence_excerpt": f"Status: Active, Edition: {active_exact.get('edition', 'Current')}, Scope: {active_exact.get('scope', '')[:100]}...",
                        "confidence_status": "VERIFIED_FACT"
                    })
                elif not year:
                    findings.append({
                        "id": f"fnd_a_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_A_SUPERSEDED",
                        "rule_name": "Unversioned Standard Reference",
                        "severity": "INFO",
                        "description": (
                            f"Standard '{norm_std}' is cited without an explicit publication year. "
                            f"The active version in the BIS catalogue is '{active_exact['standard_number']}'."
                        ),
                        "clause_excerpt": excerpt,
                        "standard_identifier": norm_std,
                        "recommended_action": (
                            f"Confirm specification intends latest edition '{active_exact['standard_number']}' "
                            f"or specify full edition explicitly to avoid supplier ambiguity."
                        ),
                        "evidence_source": "Bureau of Indian Standards Official Catalogue",
                        "evidence_record_id": active_exact["standard_number"],
                        "evidence_excerpt": f"Active edition: {active_exact['standard_number']} ({active_exact.get('edition', '')}).",
                        "confidence_status": "VERIFIED_FACT"
                    })
                continue

            # 3. If year is specified but neither matches active standard nor known supersedes:
            if year:
                # We know the base standard exists in our catalogue, but with a different year,
                # OR the standard is not in our catalogue at all.
                # Do NOT assume obsolete just because year is old; do NOT invent replacement.
                findings.append({
                    "id": f"fnd_a_{uuid.uuid4().hex[:6]}",
                    "rule_id": "RULE_A_SUPERSEDED",
                    "rule_name": "Unverified Standard Edition",
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "description": (
                        f"Edition '{norm_std}' cited in the tender cannot be verified against current catalogue lifecycle records. "
                        f"Replacement and withdrawal status is unconfirmed in available data."
                    ),
                    "clause_excerpt": excerpt,
                    "standard_identifier": norm_std,
                    "recommended_action": (
                        "Procurement officer must independently check the official BIS portal (manakonline.in) "
                        "to determine whether this edition is active, reaffirmed, or superseded."
                    ),
                    "evidence_source": "Local Curated Catalogue (21 Standards)",
                    "evidence_record_id": "UNVERIFIED_EDITION",
                    "evidence_excerpt": f"No confirmed replacement or active record for '{norm_std}' in local verified dataset.",
                    "confidence_status": "UNCERTAIN_MATCH"
                })

        return findings

    def _evaluate_rule_b(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rule B — QCO and mandatory certification:
        - Evaluate relevant products against applicable records in data/real/qco_registry.json.
        - Flag potential omission of mandatory certification only when explicitly supported.
        - Distinguish confirmed requirements from uncertain product matches.
        """
        findings = []
        has_mandatory_cert_mention = bool(self.MANDATORY_CERT_PATTERN.search(text))

        # Explicit mappings between QCO keys and specific product phrases
        qco_product_indicators = {
            "IS 694": [
                "pvc cable", "pvc electric cable", "pvc insulated cable", "building wire",
                "unsheathed cable", "lighting circuit cable", "flexible cord"
            ],
            "IS 1554 (Part 1)": [
                "heavy duty pvc cable", "armored electric cable", "armoured cable",
                "underground pvc cable", "industrial wiring cable"
            ],
            "IS 7098 (Part 1)": [
                "xlpe cable", "crosslinked polyethylene cable", "xlpe insulated cable",
                "underground xlpe cable"
            ],
            "IS 269": [
                "ordinary portland cement", "opc 43", "opc 53", "opc 33", "opc cement"
            ],
            "IS 1489 (Part 1)": [
                "portland pozzolana cement", "ppc cement", "fly ash based cement"
            ]
        }

        # Check each QCO standard in the registry
        for qco_std, qco_records in self.qco_registry.items():
            qco_base = self._extract_base_code(qco_std).upper()
            first_qco = qco_records[0] if qco_records else {}

            # Check explicit citation of standard
            is_std_explicit = False
            for raw_match in self.IS_PATTERN.findall(text):
                norm_is = self._normalize_is_string(raw_match)
                if self._extract_base_code(norm_is).upper() == qco_base:
                    is_std_explicit = True
                    break

            # Check specific product phrases
            specific_product_matched = False
            indicators = qco_product_indicators.get(qco_std, [])
            for ind in indicators:
                if re.search(r'\b' + re.escape(ind) + r'\b', text, re.IGNORECASE):
                    specific_product_matched = True
                    break

            # If either the standard is explicitly cited OR a specific product indicator matched
            if is_std_explicit or specific_product_matched:
                matched_label = qco_std if is_std_explicit else f"Product matching {qco_std}"
                excerpt, _ = self._find_clause_excerpt(
                    text,
                    qco_std if is_std_explicit else (indicators[0] if indicators else qco_std),
                    document_chunks
                )

                if has_mandatory_cert_mention:
                    findings.append({
                        "id": f"fnd_b_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_B_QCO_MANDATORY",
                        "rule_name": "Quality Control Order (QCO) Mandatory Certification",
                        "severity": "INFO",
                        "description": (
                            f"Tender includes mandatory certification / Standard Mark requirement for '{matched_label}' "
                            f"governed by '{first_qco.get('mandate', 'Quality Control Order')}'."
                        ),
                        "clause_excerpt": excerpt,
                        "standard_identifier": qco_std,
                        "recommended_action": "Verify license validity of bidders on BIS portal before contract award.",
                        "evidence_source": "data/real/qco_registry.json",
                        "evidence_record_id": qco_std,
                        "evidence_excerpt": (
                            f"Authority: {first_qco.get('authority')}; Scheme: {first_qco.get('scheme')}; "
                            f"Mandate: {first_qco.get('mandate')}; Notification: {first_qco.get('evidence_ref')}."
                        ),
                        "confidence_status": "VERIFIED_FACT"
                    })
                else:
                    findings.append({
                        "id": f"fnd_b_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_B_QCO_MANDATORY",
                        "rule_name": "Quality Control Order (QCO) Mandatory Certification",
                        "severity": "CRITICAL",
                        "description": (
                            f"Specification references '{matched_label}', which is legally governed by the mandatory Quality Control Order "
                            f"'{first_qco.get('mandate', 'Quality Control Order')}', but the tender omits the mandatory "
                            f"BIS Certification / ISI Mark requirement."
                        ),
                        "clause_excerpt": excerpt,
                        "standard_identifier": qco_std,
                        "recommended_action": (
                            f"Mandatory amendment: Incorporate statutory requirement that products must carry "
                            f"valid {first_qco.get('mark', 'ISI Mark')} under {first_qco.get('scheme')} pursuant to {first_qco.get('evidence_ref')}."
                        ),
                        "evidence_source": "data/real/qco_registry.json",
                        "evidence_record_id": qco_std,
                        "evidence_excerpt": (
                            f"Mandate: {first_qco.get('mandate')}; Status: {first_qco.get('status')}; "
                            f"Authority: {first_qco.get('authority')}; Ref: {first_qco.get('evidence_ref')}."
                        ),
                        "confidence_status": "VERIFIED_FACT"
                    })

        # Check for uncertain generic product matches without explicit standard (e.g. generic 'cable' or 'cement')
        # Do not infer that every standard in QCO applies to every product!
        if not any(f["rule_id"] == "RULE_B_QCO_MANDATORY" for f in findings):
            lower_text = text.lower()
            if re.search(r'\b(?:cables?|wires?)\b', lower_text) and not self.IS_PATTERN.search(text):
                findings.append({
                    "id": f"fnd_b_{uuid.uuid4().hex[:6]}",
                    "rule_id": "RULE_B_QCO_MANDATORY",
                    "rule_name": "Uncertain Product QCO Applicability",
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "description": (
                        "Tender mentions generic electrical cable/wire terminology without specifying the exact IS standard. "
                        "Multiple distinct Cable Quality Control Orders exist in the registry (IS 694, IS 1554, IS 7098)."
                    ),
                    "clause_excerpt": self._find_clause_excerpt(text, "cable", document_chunks)[0],
                    "standard_identifier": "Cable QCO Registry",
                    "recommended_action": (
                        "Procurement officer must determine specific cable voltage/insulation type and verify whether "
                        "statutory QCO ISI Mark requirements apply to the intended procurement item."
                    ),
                    "evidence_source": "data/real/qco_registry.json",
                    "evidence_record_id": "GENERIC_CABLE_MATCH",
                    "evidence_excerpt": "QCO registry covers IS 694 (domestic wiring), IS 1554 (heavy duty), and IS 7098 (XLPE).",
                    "confidence_status": "UNCERTAIN_MATCH"
                })

        return findings

    def _evaluate_rule_c(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rule C — Foreign standards:
        - Detect explicitly mentioned foreign standards such as ASTM or IEC identifiers.
        - Flag as WARNING for officer review when applicable Indian standard precedence cannot be established.
        - Do not automatically label foreign standard illegal.
        - Do not invent Make-in-India clause or statutory citation.
        """
        findings = []
        raw_matches = self.FOREIGN_PATTERN.findall(text)
        seen_foreign = set()

        for raw_match in raw_matches:
            clean_foreign = re.sub(r'\s+', ' ', raw_match).strip()
            # Double check it is not part of IS/IEC
            pos = text.find(raw_match)
            if pos >= 3 and text[pos-3:pos].upper() in ["IS/", "IS "]:
                continue

            if clean_foreign.upper() in seen_foreign:
                continue
            seen_foreign.add(clean_foreign.upper())

            excerpt, _ = self._find_clause_excerpt(text, raw_match, document_chunks)

            findings.append({
                "id": f"fnd_c_{uuid.uuid4().hex[:6]}",
                "rule_id": "RULE_C_FOREIGN_STANDARD",
                "rule_name": "Foreign Standard Equivalence Review",
                "severity": "WARNING",
                "description": (
                    f"Foreign standard '{clean_foreign}' is explicitly specified in the tender text. "
                    f"Officer review is required to verify Indian Standard equivalence and public procurement policy applicability."
                ),
                "clause_excerpt": excerpt,
                "standard_identifier": clean_foreign,
                "recommended_action": (
                    f"Procurement officer must independently verify whether an equivalent Indian Standard (IS) exists "
                    f"and confirm whether tender regulations permit or restrict citation of foreign standard '{clean_foreign}'."
                ),
                "evidence_source": "Tender Specification Text",
                "evidence_record_id": clean_foreign,
                "evidence_excerpt": f"Direct foreign standard mention detected: '{clean_foreign}'.",
                "confidence_status": "VERIFIED_FACT"
            })

        return findings

    def _evaluate_rule_d(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rule D — Normative references and testing:
        - Use verified relationships in the standards catalogue to identify relevant normative references and test methods.
        - Report missing references as WARNING or INFO only when supported by available data.
        - Never claim a required test is missing if the applicable requirement has not been verified.
        """
        findings = []
        raw_matches = self.IS_PATTERN.findall(text)
        processed_stds = set()

        for raw_match in raw_matches:
            norm_std = self._normalize_is_string(raw_match)
            base_code = self._extract_base_code(norm_std)
            if base_code.upper() in processed_stds:
                continue
            processed_stds.add(base_code.upper())

            # Look up standard in catalogue
            std_record = self.standards_by_num.get(norm_std)
            if not std_record:
                base_matches = self.standards_by_base.get(base_code, [])
                if base_matches:
                    std_record = base_matches[0]

            if not std_record:
                continue

            # 1. Check verified test methods
            test_methods = std_record.get("test_methods", [])
            for tm in test_methods:
                tm_num = tm.get("standard_number", "")
                tm_title = tm.get("title", "")
                tm_base = self._extract_base_code(tm_num)

                # Check if test method is cited in text
                if not re.search(r'\b' + re.escape(tm_base) + r'\b', text, re.IGNORECASE):
                    findings.append({
                        "id": f"fnd_d_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_D_NORMATIVE_TESTING",
                        "rule_name": "Normative Testing Method Verification",
                        "severity": "WARNING",
                        "description": (
                            f"Verified standard '{std_record['standard_number']}' defines mandatory test method '{tm_num}' "
                            f"({tm_title}), but this test method is not explicitly cited in the tender specification."
                        ),
                        "clause_excerpt": self._find_clause_excerpt(text, raw_match, document_chunks)[0],
                        "standard_identifier": tm_num,
                        "recommended_action": (
                            f"Verify that tender acceptance and inspection clauses explicitly require testing in accordance with "
                            f"'{tm_num}' ({tm_title}) to ensure quality compliance."
                        ),
                        "evidence_source": "Bureau of Indian Standards Official Catalogue",
                        "evidence_record_id": std_record["standard_number"],
                        "evidence_excerpt": f"Catalogue relationship: '{std_record['standard_number']}' REQUIRES_TESTING_VIA '{tm_num}'.",
                        "confidence_status": "VERIFIED_FACT"
                    })

            # 2. Check verified normative references
            normative_refs = std_record.get("normative_references", [])
            for nr in normative_refs:
                nr_num = nr.get("standard_number", "")
                nr_title = nr.get("title", "")
                nr_relation = nr.get("relation", "NORMATIVE_REFERENCE")
                nr_base = self._extract_base_code(nr_num)

                # Check if normative ref is cited in text
                if not re.search(r'\b' + re.escape(nr_base) + r'\b', text, re.IGNORECASE):
                    findings.append({
                        "id": f"fnd_d_{uuid.uuid4().hex[:6]}",
                        "rule_id": "RULE_D_NORMATIVE_TESTING",
                        "rule_name": "Normative Reference Completeness",
                        "severity": "INFO",
                        "description": (
                            f"Standard '{std_record['standard_number']}' specifies normative reference '{nr_num}' "
                            f"({nr_title}) [Relationship: {nr_relation}]."
                        ),
                        "clause_excerpt": self._find_clause_excerpt(text, raw_match, document_chunks)[0],
                        "standard_identifier": nr_num,
                        "recommended_action": (
                            f"Confirm whether technical requirements require explicit cross-referencing to '{nr_num}' "
                            f"for raw materials or auxiliary component standards."
                        ),
                        "evidence_source": "Bureau of Indian Standards Official Catalogue",
                        "evidence_record_id": std_record["standard_number"],
                        "evidence_excerpt": f"Catalogue relationship: '{std_record['standard_number']}' {nr_relation} '{nr_num}'.",
                        "confidence_status": "VERIFIED_FACT"
                    })

        return findings

    def _evaluate_rule_e(
        self,
        text: str,
        document_chunks: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rule E — Evidence and completeness:
        - Check whether identified standards and material requirements can be linked to verified catalogue records and evidence.
        - Report unsupported or unresolved items as MANUAL_REVIEW_REQUIRED.
        - Do not fabricate clause numbers, page citations, or evidence excerpts.
        """
        findings = []
        raw_matches = self.IS_PATTERN.findall(text)
        seen_unresolved = set()

        if not raw_matches:
            findings.append({
                "id": f"fnd_e_{uuid.uuid4().hex[:6]}",
                "rule_id": "RULE_E_EVIDENCE_COMPLETENESS",
                "rule_name": "Standards Grounding and Completeness",
                "severity": "WARNING",
                "description": (
                    "No explicit Indian Standards (IS) were detected in the tender specification. "
                    "Technical requirements may lack standardized national quality benchmarks."
                ),
                "clause_excerpt": text[:150] + ("..." if len(text) > 150 else ""),
                "standard_identifier": None,
                "recommended_action": (
                    "Run AI recommendation search on the procurement scope to identify and incorporate "
                    "authoritative Indian Standards prior to final approval."
                ),
                "evidence_source": "Tender Document Analysis",
                "evidence_record_id": "NO_IS_DETECTED",
                "evidence_excerpt": "Zero Indian Standard identifiers detected in submitted tender text.",
                "confidence_status": "VERIFIED_FACT"
            })
            return findings

        for raw_match in raw_matches:
            norm_std = self._normalize_is_string(raw_match)
            base_code = self._extract_base_code(norm_std)

            # Check if this standard exists anywhere in our verified catalogue (by number, base, or supersedes)
            in_by_num = norm_std in self.standards_by_num
            in_by_base = base_code in self.standards_by_base
            in_supersedes = norm_std in self.supersedes_map

            if not in_by_num and not in_by_base and not in_supersedes:
                if base_code.upper() in seen_unresolved:
                    continue
                seen_unresolved.add(base_code.upper())

                excerpt, _ = self._find_clause_excerpt(text, raw_match, document_chunks)
                findings.append({
                    "id": f"fnd_e_{uuid.uuid4().hex[:6]}",
                    "rule_id": "RULE_E_EVIDENCE_COMPLETENESS",
                    "rule_name": "Uncatalogued Standard Citation",
                    "severity": "MANUAL_REVIEW_REQUIRED",
                    "description": (
                        f"Standard '{norm_std}' cited in the tender cannot be verified against the 21 curated standards "
                        f"in the local catalogue. Grounded clause evidence and lifecycle data cannot be automatically resolved."
                    ),
                    "clause_excerpt": excerpt,
                    "standard_identifier": norm_std,
                    "recommended_action": (
                        f"Procurement officer must manually inspect the official BIS directory (manakonline.in) "
                        f"to confirm that '{norm_std}' is valid, current, and applicable to the item."
                    ),
                    "evidence_source": "Local Curated Catalogue (21 Standards)",
                    "evidence_record_id": "UNRESOLVED_RECORD",
                    "evidence_excerpt": f"No authoritative catalogue record present in local verified database for '{norm_std}'.",
                    "confidence_status": "UNCERTAIN_MATCH"
                })

        return findings
