"""
Evidence Verifier: Enforces evidence-first grounding for every recommendation.
Extracts grounded evidence snippets directly from document metadata and chunk records.
Rejects ungrounded claims and strictly returns 'Insufficient evidence' if unsupported.
"""
from typing import Dict, Any, List, Optional

class EvidenceVerifier:
    """Verifies that a recommendation is substantiated by explicit text evidence
    originating strictly from stored document metadata, never from LLM hallucination."""

    def verify(
        self,
        standard_payload: Dict[str, Any],
        query_text: str = "",
        document_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extracts cited text evidence, page numbers, section clauses, and source references.
        Populates both singular fields ('evidence_text', 'page', 'section') and 'evidence_list'.
        Substantiates claims using uploaded document chunks and authoritative catalogue scope.
        """
        std_num = standard_payload.get("standard_number", "")
        std_num_clean = std_num.lower().replace("-", " ").replace(":", " ")
        std_title = (standard_payload.get("title") or "").lower()
        std_keywords = [k.lower() for k in standard_payload.get("keywords") or []]
        std_scope = (standard_payload.get("scope") or "").strip()
        source = standard_payload.get("source", "Bureau of Indian Standards")

        evidence_snippets: List[Dict[str, Any]] = []

        # 1. Check matching text from uploaded document chunks if available
        if document_chunks:
            for c in document_chunks:
                chunk_content = c.get("content") or c.get("text") or ""
                chunk_lower = chunk_content.lower()
                chunk_page = c.get("page_number") or c.get("page", 1)
                chunk_section = c.get("section") or f"Page {chunk_page}"
                chunk_source = c.get("filename") or "Uploaded Tender Document"

                # Check if document explicitly cites the standard code
                has_code_mention = (
                    std_num.lower() in chunk_lower or
                    (len(std_num) > 5 and std_num.split(":")[0].lower() in chunk_lower)
                )

                # Check technical term overlap with standard keywords/title
                matched_kw = [k for k in std_keywords if k in chunk_lower]
                has_term_match = len(matched_kw) >= 2 or any(k in chunk_lower for k in ["pvc cable", "xlpe cable", "steel tube", "pipe", "concrete", "cement"] if k in std_title or k in std_keywords)

                if has_code_mention or (has_term_match and len(chunk_content) > 30):
                    snippet_text = chunk_content.strip()
                    if len(snippet_text) > 400:
                        snippet_text = snippet_text[:400] + "..."
                    evidence_snippets.append({
                        "text": snippet_text,
                        "page": chunk_page,
                        "section": chunk_section,
                        "source": f"{chunk_source} (Page {chunk_page})"
                    })
                    break  # Keep the best chunk snippet

        # 2. Check evidence from chunk-level payload or evidence_sample
        evidence_sample = standard_payload.get("evidence_sample")
        if isinstance(evidence_sample, dict) and evidence_sample.get("text"):
            sample_text = evidence_sample.get("text", "").strip()
            if len(sample_text) >= 15:
                evidence_snippets.append({
                    "text": sample_text,
                    "page": evidence_sample.get("page", 1),
                    "section": evidence_sample.get("section", "General"),
                    "source": source
                })

        # 3. Check official catalogue scope grounding if query text aligns
        if not evidence_snippets and std_scope and len(std_scope) >= 20:
            query_lower = query_text.lower()
            # Verify that query actually aligns with standard before citing scope
            matching_terms = [k for k in std_keywords if k in query_lower]
            std_in_query = (std_num.lower() in query_lower) or (len(std_num) > 5 and std_num.split(":")[0].lower() in query_lower)
            product_words = [w for w in ["cable", "conductor", "concrete", "cement", "steel", "pipe", "water", "bolt"] if w in std_title or w in std_keywords]
            has_prod_overlap = any(w in query_lower for w in product_words)

            if std_in_query or matching_terms or has_prod_overlap:
                evidence_snippets.append({
                    "text": std_scope,
                    "page": 1,
                    "section": "Clause 1 - Scope",
                    "source": f"{source} ({std_num})"
                })

        # Validation: If no substantiated evidence could be found
        if not evidence_snippets:
            return {
                "verified": False,
                "evidence_text": "Insufficient evidence",
                "page": None,
                "section": None,
                "source": source or "Unknown",
                "evidence_list": [],
                "confidence": 0.0,
                "audit_status": "Insufficient evidence - No grounded citation available"
            }

        primary = evidence_snippets[0]
        return {
            "verified": True,
            "evidence_text": primary["text"],
            "page": primary.get("page"),
            "section": primary.get("section", "General Section"),
            "source": primary.get("source", source),
            "evidence_list": evidence_snippets,
            "confidence": 0.95,
            "audit_status": "Grounded in Authoritative Source Document"
        }
