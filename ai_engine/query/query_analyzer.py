"""
Query Analyzer: Decomposes natural language procurement requirements or technical
specifications into structured domain concepts, entity tags, and search constraints.
Phase 4: Integrates LLM query understanding with deterministic rule extractor fallback.
"""
from typing import Dict, List, Any, Optional
import os
import re
import logging

from ai_engine.query.schema import StructuredRequirements
from ai_engine.query.rule_extractor import RuleExtractor
from ai_engine.query.llm_provider import get_llm_provider, BaseLLMProvider
from ai_engine.query.multilingual import MultilingualNormalizer, tokenize_unicode

logger = logging.getLogger("sih26108.query")

class QueryAnalyzer:
    """Analyzes procurement queries to extract technical concepts, electrical parameters,
    and environmental conditions with multilingual script detection and normalization."""

    DOMAIN_KEYWORDS = {
        "electrical": ["cable", "wire", "voltage", "current", "conductor", "insulation", "pvc", "xlpe", "power", "wiring", "transformer"],
        "waterproofing": ["waterproof", "water", "moisture", "damp", "submersible", "immersion", "ip67", "ip68", "ingress"],
        "civil_building": ["building", "residential", "commercial", "conduit", "duct", "trench", "flooring", "structural", "concrete", "steel", "cement", "aggregate"],
        "fire_safety": ["flame", "fire", "smoke", "flammability", "toxic", "frls", "heat resistant"]
    }

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider
        self.rule_extractor = RuleExtractor()
        self.multilingual_normalizer = MultilingualNormalizer(provider=provider)

    def _get_provider(self) -> BaseLLMProvider:
        if self.provider is not None:
            return self.provider
        return get_llm_provider()

    def extract_structured_requirements(self, query: str) -> StructuredRequirements:
        """
        Extracts structured requirements with LLM understanding and deterministic fallback:
        User query -> LLM understanding when configured -> validate StructuredRequirements
        -> fallback to rule extractor if LLM unavailable.
        """
        if not query or not query.strip():
            return StructuredRequirements()

        provider = self._get_provider()
        structured: Optional[StructuredRequirements] = None

        if provider.is_available():
            try:
                structured = provider.parse_query(query)
            except Exception as e:
                logger.warning(f"LLM query understanding exception: {type(e).__name__}. Falling back to rule extractor.")

        # Fall back to deterministic rule extractor if LLM returned None or is not available
        if structured is None:
            structured = self.rule_extractor.extract(query)

        return structured

    def analyze(self, query: str) -> Dict[str, Any]:
        """Extracts technical concepts, identified domains, and cleaned search tokens with multilingual support."""
        if not query or not query.strip():
            return {
                "raw_query": "",
                "original_query": "",
                "clean_tokens": [],
                "detected_domains": [],
                "concepts": {
                    "materials": [],
                    "environments": [],
                    "specifications": []
                },
                "structured_requirements": None,
                "llm_used": False,
                "llm_provider": "none",
                "is_empty": True,
                "detected_language": "unknown",
                "detected_script": "Unknown",
                "normalized_english_query": "",
                "normalization_method": "INCOMPLETE",
                "normalization_status": "INCOMPLETE",
                "normalization_message": "Empty query provided."
            }

        cleaned = query.strip()

        # Step 1: Multilingual Detection & Normalization (Feature M9)
        provider = self._get_provider()
        multi_result = self.multilingual_normalizer.normalize(cleaned)
        detected_lang = multi_result.get("detected_language", "en")
        norm_status = multi_result.get("normalization_status", "UNCHANGED")

        # Determine effective English text for domain and concept extraction
        if detected_lang == "en":
            effective_query = cleaned
        elif norm_status == "SUCCESS" and multi_result.get("normalized_english_query"):
            effective_query = multi_result["normalized_english_query"]
        else:
            effective_query = ""

        effective_lower = effective_query.lower()

        # Step 2: Identify relevant domains
        detected_domains = []
        if effective_lower:
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                if any(re.search(r'\b' + re.escape(kw) + r'\b', effective_lower) for kw in keywords):
                    detected_domains.append(domain)

        # Step 3: Detect specific environmental/material concepts
        materials = [m for m in ["pvc", "xlpe", "copper", "aluminum", "steel", "concrete", "cement"] if m in effective_lower]
        environments = [e for e in ["waterproof", "damp", "outdoor", "underground", "submerged", "building", "hazardous"] if e in effective_lower]

        # Step 4: Unicode-Safe Token extraction
        tokens = list(multi_result.get("clean_tokens", []))
        if not tokens:
            tokens = tokenize_unicode(cleaned)

        # Step 5: Phase 4 Structured Requirements Extraction
        structured_reqs: Optional[StructuredRequirements] = None
        llm_used = multi_result.get("normalization_method") == "LLM"

        if effective_query:
            if provider.is_available() and getattr(provider, "__class__", type(provider)).__name__ != "MockLLMProvider":
                try:
                    structured_reqs = provider.parse_query(effective_query)
                    if structured_reqs is not None:
                        llm_used = True
                except Exception as e:
                    logger.warning(f"LLM query understanding exception: {type(e).__name__}. Falling back to rule extractor.")

            # Fall back to deterministic rule extractor if LLM returned None or is not available
            if structured_reqs is None:
                structured_reqs = self.rule_extractor.extract(effective_query)

        structured_dict = structured_reqs.to_dict() if structured_reqs else None

        # Enrich tokens and domains with structured concepts if present
        if structured_reqs:
            if structured_reqs.product and structured_reqs.product.lower() not in effective_lower:
                tokens.extend(tokenize_unicode(structured_reqs.product.lower()))
            if structured_reqs.foreign_standards:
                tokens.extend(structured_reqs.foreign_standards)

        return {
            "raw_query": cleaned,
            "original_query": cleaned,
            "clean_tokens": list(dict.fromkeys(tokens)),
            "detected_domains": detected_domains or (["general_engineering"] if effective_query else []),
            "concepts": {
                "materials": materials,
                "environments": environments,
                "specifications": [f"Domain: {d}" for d in detected_domains]
            },
            "structured_requirements": structured_dict,
            "llm_used": llm_used,
            "llm_provider": provider.__class__.__name__,
            "is_empty": False,
            # Feature M9 Multilingual fields:
            "detected_language": multi_result.get("detected_language", "en"),
            "detected_script": multi_result.get("detected_script", "Latin"),
            "response_language": multi_result.get("response_language", "en"),
            "response_language_name": multi_result.get("response_language_name", "English"),
            "normalized_english_query": multi_result.get("normalized_english_query"),
            "normalization_method": multi_result.get("normalization_method", "UNCHANGED_ENGLISH"),
            "normalization_status": multi_result.get("normalization_status", "UNCHANGED"),
            "normalization_message": multi_result.get("normalization_message", "")
        }
