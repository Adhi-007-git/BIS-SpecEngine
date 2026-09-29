"""
Recommendation Generator: Synthesizes ranked standards, verified evidence,
normative graph relations, and compliance mandates into structured recommendations.
Preserves existing 'evidence', 'page', and 'section' while attaching 'evidence_list'
and transparent scoring factor breakdowns.
"""
from typing import List, Dict, Any

from ai_engine.recommendation.multilingual_response import MultilingualResponseGenerator

class RecommendationGenerator:
    """Produces explainable recommendation items adhering strictly to evidence-first rules."""

    def build_recommendations(
        self,
        reranked_candidates: List[Dict[str, Any]],
        verified_evidence_map: Dict[str, Dict[str, Any]],
        compliance_map: Dict[str, List[Dict[str, Any]]],
        related_standards_map: Dict[str, List[Dict[str, Any]]],
        query_analysis: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Constructs the final list of recommendation objects with comprehensive compliance and lifecycle provenance."""
        recommendations: List[Dict[str, Any]] = []

        foreign_standards_in_query = []
        response_lang = "en"
        if query_analysis and isinstance(query_analysis, dict):
            response_lang = query_analysis.get("response_language") or query_analysis.get("detected_language") or "en"
            sr = query_analysis.get("structured_requirements")
            if sr and isinstance(sr, dict):
                foreign_standards_in_query = sr.get("foreign_standards") or []

        for candidate in reranked_candidates:
            # Filter out incompatible product categories
            if candidate.get("category_incompatible"):
                continue

            # Hard Rated Voltage Conflict Filter: Exclude candidates whose voltage rating is exceeded
            if candidate.get("voltage_incompatible"):
                continue

            # Hard Insulation Material Conflict Filter: Exclude candidates with conflicting dielectric insulation
            if candidate.get("insulation_incompatible"):
                continue

            calibrated_score = candidate.get("calibrated_score", round(candidate.get("score", 0.5), 4))
            if calibrated_score < 0.25:
                continue

            payload = candidate.get("payload", {})
            std_num = payload.get("standard_number", "UNKNOWN-IS")

            evidence_data = verified_evidence_map.get(std_num, {})
            compliance_list = compliance_map.get(std_num, [])
            related_list = related_standards_map.get(std_num, [])
            ranking_reasons = candidate.get("ranking_reasons", [])
            score_factors = candidate.get("score_factors")

            # QCO enforcement: Only True if standard has verified mandatory status in official registry
            qco_enforcement_flag = bool(
                compliance_list and any(
                    c.get("status") == "Mandatory for Procurement"
                    for c in compliance_list
                )
            )

            # Construct human-readable justification in the requested response language
            reason_summary = MultilingualResponseGenerator.format_reasoning(
                reasons=ranking_reasons,
                standard_number=std_num,
                title=payload.get("title", ""),
                response_lang=response_lang,
                qco_mandatory=qco_enforcement_flag
            )

            # Evidence handling
            primary_evidence_text = evidence_data.get("evidence_text", "Insufficient evidence")
            evidence_list = evidence_data.get("evidence_list", [])
            if not evidence_list and primary_evidence_text != "Insufficient evidence":
                evidence_list = [
                    {
                        "text": primary_evidence_text,
                        "page": evidence_data.get("page"),
                        "section": evidence_data.get("section"),
                        "source": payload.get("source", "Bureau of Indian Standards")
                    }
                ]

            has_grounded_evidence = evidence_data.get("verified", False) and primary_evidence_text != "Insufficient evidence"

            # Task 2 & 4: Adequate support requirement
            # A candidate must have grounded evidence or substantive domain/category/technical alignment.
            has_substantive_alignment = (
                any("Product category verified" in r for r in ranking_reasons) or
                any("Specified material verified" in r for r in ranking_reasons) or
                any("Operating voltage verified" in r for r in ranking_reasons) or
                any("Capacity rating verified" in r for r in ranking_reasons) or
                any("Direct reference to standard code" in r for r in ranking_reasons)
            )

            if not has_grounded_evidence and not has_substantive_alignment:
                continue

            is_demo = payload.get("is_demo", True)
            if is_demo:
                demo_tag = payload.get("demo_tag", "DEMO DATA")
            elif has_grounded_evidence:
                demo_tag = "VERIFIED SOURCE"
            else:
                demo_tag = "REVIEW REQUIRED"

            # Extended fields for full compliance & lifecycle auditing
            lifecycle_status = payload.get("status", "Active")
            last_verified = payload.get("last_verified")
            normative_refs = payload.get("normative_references", [])
            if not normative_refs and related_list:
                normative_refs = [r for r in related_list if r.get("relation") == "NORMATIVE_REFERENCE"]

            applicable_scheme = compliance_list[0].get("scheme") if compliance_list else None
            compliance_alerts = MultilingualResponseGenerator.format_compliance_alerts(compliance_list, response_lang)

            applicability_type = candidate.get("applicability_type", "DIRECTLY_APPLICABLE")
            exclusion_reason = MultilingualResponseGenerator.format_exclusion_reason(candidate.get("exclusion_reason"), response_lang)
            officer_verification_needed = candidate.get("officer_verification_needed", False)

            # Foreign standard notice in requested response language
            foreign_standard_warning = None
            if foreign_standards_in_query:
                for fs in foreign_standards_in_query:
                    fs_clean = fs.upper().strip()
                    # Case A: Identical / harmonized adoptions (e.g. IEC 60529 -> IS/IEC 60529:2001)
                    if "IS/IEC" in std_num.upper() and any(part in std_num.upper() for part in fs_clean.split()):
                        foreign_standard_warning = MultilingualResponseGenerator.format_foreign_warning(fs, std_num, response_lang)
                        break
                    # Case B: Verified structural steel equivalency (ASTM A36 -> IS 2062)
                    elif "ASTM A36" in fs_clean and "IS 2062" in std_num:
                        foreign_standard_warning = MultilingualResponseGenerator.format_foreign_warning(fs, std_num, response_lang)
                        break

            title_explanation = MultilingualResponseGenerator.get_title_explanation(std_num, response_lang)
            next_steps = MultilingualResponseGenerator.format_next_steps({"standard_number": std_num, "qco_enforcement_flag": qco_enforcement_flag}, response_lang)

            item = {
                "standard_number": std_num,
                "title": payload.get("title", ""),
                "relevance_score": calibrated_score,
                "reason": reason_summary,
                "status": lifecycle_status,
                "source": payload.get("source", "Bureau of Indian Standards Official Catalogue"),
                # Backward-compatible fields
                "evidence": primary_evidence_text,
                "page": evidence_data.get("page"),
                "section": evidence_data.get("section"),
                # Phase 2 structured fields
                "evidence_list": evidence_list,
                "score_factors": score_factors,
                "related_standards": related_list,
                "compliance": compliance_list,
                "is_demo": is_demo,
                "demo_tag": demo_tag,
                # Extended Phase 6/Final metadata fields
                "lifecycle_status": lifecycle_status,
                "last_verified": last_verified,
                "normative_references": normative_refs,
                "qco_enforcement_flag": qco_enforcement_flag,
                "applicable_scheme": applicable_scheme,
                "compliance_alerts": compliance_alerts,
                "foreign_standard_warning": foreign_standard_warning,
                "applicability_type": applicability_type,
                "exclusion_reason": exclusion_reason,
                "officer_verification_needed": officer_verification_needed,
                "title_explanation": title_explanation,
                "next_steps": next_steps,
                "applicability_reasoning": reason_summary
            }
            recommendations.append(item)

        return recommendations
