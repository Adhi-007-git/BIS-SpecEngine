"""
Reranker: Performs secondary contextual re-ranking over candidate standards and chunks.
Implements an initial configurable heuristic combining semantic similarity (40%),
material match (20%), environment/application match (20%), and technical term alignment (20%).
Exposes individual score components for transparency and empirical evaluation.
"""
from typing import List, Dict, Any, Optional

class Reranker:
    """Configurable contextual re-ranker scoring candidate standards against query concepts."""

    # Initial configurable heuristic weights
    DEFAULT_WEIGHTS = {
        "semantic": 0.40,
        "material": 0.20,
        "environment": 0.20,
        "technical_alignment": 0.20
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = dict(self.DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Re-scores candidates based on transparent weighted heuristic:
        - semantic_score: 40%
        - material_score: 20%
        - environment_score: 20%
        - technical_alignment_score: 20%
        """
        if not candidates:
            return []

        tokens = set(query_analysis.get("clean_tokens", []))
        concepts = query_analysis.get("concepts", {})
        materials = set(concepts.get("materials", []))
        environments = set(concepts.get("environments", []))
        query_lower = query.lower()

        # Phase 4/M9: Structured Requirements (Product category & technical attributes)
        structured_reqs = query_analysis.get("structured_requirements") or {}
        query_product = (structured_reqs.get("product") or "").lower().strip()
        query_capacity = (structured_reqs.get("capacity") or "").lower().strip()
        query_cooling = (structured_reqs.get("cooling") or "").lower().strip()
        query_installation = (structured_reqs.get("installation") or "").lower().strip()
        query_voltages = [
            v.lower().strip()
            for v in [structured_reqs.get("primary_voltage"), structured_reqs.get("secondary_voltage")]
            if v
        ]

        # Extract explicit technical parameters for hard compatibility verification
        add_params = structured_reqs.get("additional_parameters") or {}
        query_voltage_volts = add_params.get("rated_voltage_volts")
        if query_voltage_volts is None and query_voltages:
            from ai_engine.query.rule_extractor import parse_voltage_to_volts
            for v_str in query_voltages:
                v_num = parse_voltage_to_volts(v_str)
                if v_num is not None:
                    query_voltage_volts = max(query_voltage_volts or 0.0, v_num)
        if query_voltage_volts is None:
            from ai_engine.query.rule_extractor import parse_voltage_to_volts
            query_voltage_volts = parse_voltage_to_volts(query)

        query_insulation = add_params.get("insulation_material")
        if not query_insulation:
            if "pvc" in materials or "pvc" in query_lower or "पीवीसी" in query:
                query_insulation = "pvc"
            elif "xlpe" in materials or "xlpe" in query_lower or "एक्सएलपीई" in query:
                query_insulation = "xlpe"

        query_duty = add_params.get("duty_type")
        if not query_duty:
            if any(k in query_lower for k in ["heavy duty", "heavy-duty", "armoured", "armored", "industrial", "भारी"]):
                query_duty = "heavy_duty"
            elif any(k in query_lower for k in ["light duty", "light-duty", "domestic", "unsheathed", "lighting"]):
                query_duty = "light_duty"

        # Domain & Category knowledge for official Indian Standards catalogue
        standard_category_map = {
            "IS 456:2000": {"category": "concrete", "domain": "civil", "terms": ["concrete", "reinforced concrete", "plain concrete", "rcc"]},
            "IS 800:2007": {"category": "structural steel", "domain": "civil", "terms": ["structural steel", "steel construction", "steel structure"]},
            "IS 383:2016": {"category": "concrete aggregate", "domain": "civil", "terms": ["aggregate", "coarse aggregate", "fine aggregate", "sand", "gravel"]},
            "IS 1786:2008": {"category": "deformed steel bar", "domain": "civil", "terms": ["tmt bar", "deformed steel bar", "reinforcement steel", "steel bar"]},
            "IS 2062:2011": {"category": "structural steel", "domain": "civil", "terms": ["structural steel", "steel plate", "hot rolled steel", "steel section"]},
            "IS 694:2010": {
                "category": "pvc insulated cable",
                "domain": "electrical",
                "insulation": "pvc",
                "max_voltage_volts": 750.0,
                "voltage_str": "up to and including 450/750 V",
                "duty": "light_duty",
                "terms": ["pvc cable", "pvc insulated cable", "building wiring", "electric cable", "cable"]
            },
            "IS 1554 (Part 1):1988": {
                "category": "pvc insulated cable",
                "domain": "electrical",
                "insulation": "pvc",
                "max_voltage_volts": 1100.0,
                "voltage_str": "up to and including 1100 V",
                "duty": "heavy_duty",
                "terms": ["heavy duty cable", "pvc cable", "armored cable", "power cable", "electric cable", "cable"]
            },
            "IS/IEC 60529:2001": {"category": "enclosure", "domain": "electrical", "terms": ["ip code", "ingress protection", "enclosure", "degrees of protection"]},
            "IS 732:2019": {"category": "conduit", "domain": "electrical", "terms": ["electrical wiring", "wiring code", "installation wiring"]},
            "IS 7098 (Part 1):1988": {
                "category": "xlpe insulated cable",
                "domain": "electrical",
                "insulation": "xlpe",
                "max_voltage_volts": 1100.0,
                "voltage_str": "up to and including 1100 V",
                "duty": "heavy_duty",
                "terms": ["xlpe cable", "xlpe insulated cable", "power cable", "cable"]
            },
            "IS 269:2015": {"category": "portland cement", "domain": "civil", "terms": ["cement", "portland cement", "opc", "ordinary portland cement"]},
            "IS 1079:2017": {"category": "structural steel", "domain": "mechanical", "terms": ["steel sheet", "steel strip", "carbon steel"]},
            "IS 516:1959": {"category": "concrete testing", "domain": "testing", "terms": ["concrete testing", "compressive strength of concrete"]},
            "IS 1489 (Part 1):2015": {"category": "portland cement", "domain": "civil", "terms": ["cement", "ppc", "portland pozzolana cement", "fly ash"]},
            "IS 3025 (Part 1):1987": {"category": "water testing", "domain": "testing", "terms": ["water testing", "wastewater sampling", "water sampling"]},
            "IS 10500:2012": {"category": "drinking water", "domain": "environmental", "terms": ["drinking water", "potable water", "water quality"]},
            "IS 1363 (Part 1):2002": {"category": "fasteners", "domain": "mechanical", "terms": ["bolts", "screws", "nuts", "fasteners", "hexagon head"]},
            "IS 2386 (Part 1):1963": {"category": "aggregate testing", "domain": "testing", "terms": ["aggregate testing", "particle size test"]},
            "IS 4984:2016": {"category": "pipes", "domain": "plumbing", "terms": ["pe pipes", "polyethylene pipes", "water supply pipes"]},
            "IS 1239 (Part 1):2004": {"category": "steel tubes", "domain": "plumbing", "terms": ["steel tubes", "pipes", "tubulars", "plumbing fittings"]},
            "IS 8130:2013": {
                "category": "conductors",
                "domain": "electrical",
                "is_normative_reference_only": True,
                "terms": ["conductors", "cable conductors", "copper conductor", "aluminum conductor", "flexible cords"]
            }
        }

        reranked = []
        for item in candidates:
            payload = item.get("payload", {})
            raw_sim = float(item.get("score", 0.5))
            semantic_score = max(0.0, min(1.0, raw_sim))

            title = payload.get("title", "").lower()
            scope = payload.get("scope", "").lower()
            keywords = [k.lower() for k in payload.get("keywords", [])]
            std_num = payload.get("standard_number", "").strip()
            std_num_lower = std_num.lower()
            combined_corpus = f"{title} {scope} {' '.join(keywords)} {std_num_lower}"

            reasons = []
            category_incompatible = False
            voltage_incompatible = False
            insulation_incompatible = False
            is_directly_applicable = True
            applicability_type = "DIRECTLY_APPLICABLE"
            exclusion_reason = None
            officer_verification_needed = False

            std_cat_info = standard_category_map.get(std_num, {})

            # ── Product Category Compatibility Check ────────────────────────
            if query_product:
                product_tokens = [p for p in query_product.split() if len(p) > 2]
                cat_terms = std_cat_info.get("terms", []) + keywords
                std_category = std_cat_info.get("category", "")
                
                # Check if query product or its tokens match this standard's domain category or terms
                has_category_match = (
                    query_product in std_category or
                    std_category in query_product or
                    any(term in query_product or query_product in term for term in cat_terms) or
                    any(any(pt in term for term in cat_terms) for pt in product_tokens) or
                    any(pt in title or pt in scope for pt in product_tokens)
                )

                if "transformer" in query_product:
                    # Specific safeguard: None of the 21 catalogue standards cover transformers
                    if "transformer" not in combined_corpus:
                        category_incompatible = True
                        reasons.append(f"Incompatible product category: standard does not cover '{query_product}'.")
                elif "cable" in query_product or "wire" in query_product:
                    if not any(k in combined_corpus for k in ["cable", "conductor", "cord", "wire"]):
                        category_incompatible = True
                        reasons.append(f"Incompatible product category: standard does not cover '{query_product}'.")
                elif "pipe" in query_product or "tube" in query_product:
                    if not any(k in combined_corpus for k in ["pipe", "tube", "tubular"]):
                        category_incompatible = True
                        reasons.append(f"Incompatible product category: standard does not cover '{query_product}'.")
                elif "cement" in query_product:
                    if "cement" not in combined_corpus:
                        category_incompatible = True
                        reasons.append(f"Incompatible product category: standard does not cover '{query_product}'.")
                elif not has_category_match:
                    category_incompatible = True
                    reasons.append(f"Incompatible product category: standard does not cover '{query_product}'.")

                if has_category_match and not category_incompatible:
                    reasons.append(f"Product category verified: {query_product.upper()}")

            # ── Hard Rated Voltage Compatibility Check ──────────────────────
            if query_voltage_volts is not None and "max_voltage_volts" in std_cat_info:
                max_v = std_cat_info["max_voltage_volts"]
                if query_voltage_volts > max_v:
                    voltage_incompatible = True
                    is_directly_applicable = False
                    applicability_type = "EXCLUDED_VOLTAGE_CONFLICT"
                    v_raw = add_params.get("voltage_raw") or f"{int(query_voltage_volts)} V"
                    exclusion_reason = (
                        f"Excluded as direct match: Rated voltage conflict. "
                        f"Query specifies {v_raw} ({int(query_voltage_volts)} V), which exceeds {std_num} "
                        f"verified scope ({std_cat_info.get('voltage_str', f'max {int(max_v)} V')})."
                    )
                    reasons.append(exclusion_reason)
                else:
                    reasons.append(f"Operating voltage verified: {int(query_voltage_volts)} V matches rated scope ({std_cat_info.get('voltage_str')})")

            # ── Hard Insulation Material Compatibility Check ────────────────
            if query_insulation and "insulation" in std_cat_info:
                std_ins = std_cat_info["insulation"]
                if std_ins != query_insulation:
                    insulation_incompatible = True
                    is_directly_applicable = False
                    exclusion_reason = (
                        f"Excluded as direct match: Insulation material conflict. "
                        f"Query specifies {query_insulation.upper()} insulation; {std_num} verified scope specifies {std_ins.upper()} insulation."
                    )
                    if not voltage_incompatible and not category_incompatible:
                        applicability_type = "RELATED_REFERENCE"
                        reasons.append(
                            f"Related reference only: Alternative dielectric material ({std_ins.upper()}). "
                            f"Query specifies {query_insulation.upper()} insulation; {std_num} specifies {std_ins.upper()} insulation for working voltages up to {int(std_cat_info.get('max_voltage_volts', 1100))} V."
                        )
                    else:
                        applicability_type = "EXCLUDED_INSULATION_CONFLICT"
                        reasons.append(exclusion_reason)
                else:
                    reasons.append(f"Specified material verified: {query_insulation.upper()} insulation")

            # ── Normative Reference Standards Check ────────────────────────
            if std_cat_info.get("is_normative_reference_only"):
                is_directly_applicable = False
                applicability_type = "RELATED_REFERENCE"
                reasons.append(f"Related reference: {std_num} specifies conductor materials rather than complete cable assembly.")

            # ── Missing Parameters / Technical Uncertainty Flags ───────────
            is_cable_query = bool(query_product and ("cable" in query_product or "wire" in query_product))
            if is_cable_query and not category_incompatible:
                if query_voltage_volts is None and not any("Operating voltage verified" in r for r in reasons):
                    reasons.append("Officer verification required: Operating voltage not explicitly specified in query.")
                    officer_verification_needed = True
                if query_insulation is None and not any("insulation" in r for r in reasons):
                    reasons.append("Officer verification required: Dielectric insulation material not explicitly specified in query.")
                    officer_verification_needed = True

            # 1. Material Match Score (20%)
            if materials:
                matched_materials = [m for m in materials if m in combined_corpus]
                if matched_materials and not category_incompatible and not insulation_incompatible:
                    material_score = min(1.0, len(matched_materials) / len(materials))
                    if not any("Specified material verified" in r for r in reasons):
                        reasons.append(f"Specified material verified: {', '.join(matched_materials).upper()}")
                else:
                    material_score = 0.0
            else:
                material_score = 0.0 if (category_incompatible or insulation_incompatible) else 0.5

            # 2. Environment & Application Match Score (20%)
            if environments:
                matched_env = [e for e in environments if e in combined_corpus]
                if matched_env and not category_incompatible:
                    environment_score = min(1.0, len(matched_env) / len(environments))
                    reasons.append(f"Operating condition verified: {', '.join(matched_env)}")
                else:
                    environment_score = 0.0
            else:
                environment_score = 0.0 if category_incompatible else 0.5

            # 3. Technical Term Alignment & Standard Reference Score (20%)
            if category_incompatible or voltage_incompatible:
                technical_score = 0.0
                semantic_score = min(0.15, semantic_score * 0.3)
            else:
                tech_matches = [t for t in tokens if t in combined_corpus]
                token_ratio = len(tech_matches) / max(1, len(tokens))

                # Technical attribute bonuses (voltage, rating)
                attr_bonus = 0.0
                for v in query_voltages:
                    v_clean = v.replace(" ", "")
                    if (v in combined_corpus or v_clean in combined_corpus) and not voltage_incompatible:
                        attr_bonus += 0.25
                        if not any("Operating voltage verified" in r for r in reasons):
                            reasons.append(f"Operating voltage verified: {v.upper()}")

                if query_capacity and query_capacity in combined_corpus:
                    attr_bonus += 0.2
                    reasons.append(f"Capacity rating verified: {query_capacity}")

                # Bonus for explicit standard code mention
                std_exact_bonus = 0.5 if std_num_lower and std_num_lower in query_lower else 0.0
                if std_exact_bonus > 0:
                    reasons.append(f"Direct reference to standard code {payload.get('standard_number')}")
                
                technical_score = min(1.0, (token_ratio * 0.6) + std_exact_bonus + attr_bonus)
                if len(tech_matches) >= 2 and not any("Direct reference" in r for r in reasons):
                    reasons.append(f"Technical terminology alignment ({len(tech_matches)} matched tokens)")

            # Compute Weighted Final Score
            w_sem = self.weights["semantic"]
            w_mat = self.weights["material"]
            w_env = self.weights["environment"]
            w_tech = self.weights["technical_alignment"]

            weighted_sum = (
                (semantic_score * w_sem) +
                (material_score * w_mat) +
                (environment_score * w_env) +
                (technical_score * w_tech)
            )

            if category_incompatible or voltage_incompatible:
                final_score = round(min(0.12, max(0.02, weighted_sum * 0.2)), 4)
            elif insulation_incompatible:
                # Downgrade score for conflicting insulation material below direct applicability
                final_score = round(min(0.22, max(0.05, weighted_sum * 0.4)), 4)
            else:
                final_score = round(min(0.99, max(0.10, weighted_sum)), 4)

            score_factors = {
                "semantic_score": round(semantic_score, 4),
                "material_score": round(material_score, 4),
                "environment_score": round(environment_score, 4),
                "technical_alignment_score": round(technical_score, 4),
                "final_score": final_score,
                "weights_used": self.weights,
                "heuristic_note": "Configurable initial heuristic (40% semantic, 20% material, 20% environment, 20% technical alignment)"
            }

            item_copy = dict(item)
            item_copy["calibrated_score"] = final_score
            item_copy["score_factors"] = score_factors
            item_copy["category_incompatible"] = category_incompatible
            item_copy["voltage_incompatible"] = voltage_incompatible
            item_copy["insulation_incompatible"] = insulation_incompatible
            item_copy["is_directly_applicable"] = is_directly_applicable
            item_copy["applicability_type"] = applicability_type
            item_copy["exclusion_reason"] = exclusion_reason
            item_copy["officer_verification_needed"] = officer_verification_needed
            item_copy["ranking_reasons"] = reasons or ["Retrieved via semantic proximity to procurement specification"]
            reranked.append(item_copy)

        # Sort descending by calibrated score
        reranked.sort(key=lambda x: x["calibrated_score"], reverse=True)
        return reranked
