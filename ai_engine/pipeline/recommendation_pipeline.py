"""
Recommendation Pipeline: Orchestrates the end-to-end evidence-first AI flow:
User Query -> Query Analyzer -> Query Embedding -> Vector Search ->
Top-k Chunks -> Re-ranking -> Evidence Verification -> Knowledge Graph Links ->
Recommendation Generator -> Structured Response.
Also manages the Document Ingestion pipeline:
PDF/TXT -> Parser -> Page-Preserved Text -> Cleaning -> Chunking -> Metadata -> Embedding -> Qdrant.
"""
from typing import Dict, Any, List, Optional
import uuid
import logging

from ai_engine.query.query_analyzer import QueryAnalyzer
from ai_engine.embeddings.embedding_service import EmbeddingService
from ai_engine.vector_db.qdrant_service import QdrantService
from ai_engine.search.search_engine import SearchEngine
from ai_engine.reranker.reranker import Reranker
from ai_engine.knowledge_graph.neo4j_service import Neo4jService
from ai_engine.knowledge_graph.graph_builder import GraphBuilder
from ai_engine.compliance.compliance_engine import ComplianceEngine
from ai_engine.verification.evidence_verifier import EvidenceVerifier
from ai_engine.recommendation.recommendation_generator import RecommendationGenerator
from ai_engine.documents.pdf_parser import PDFParser
from ai_engine.documents.text_extractor import TextExtractor
from ai_engine.documents.chunker import DocumentChunker
from ai_engine.documents.document_ingestion_service import DocumentIngestionService

logger = logging.getLogger(__name__)

class RecommendationPipeline:
    """Master pipeline orchestrating modular AI, retrieval, and document ingestion services."""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "sih_password"
    ):
        # 1. Independent Core Services
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService(url=qdrant_url)
        self.document_ingestion_service = DocumentIngestionService(self.embedding_service, self.qdrant_service)
        # Alias so upload route can access via getattr(pipeline, "ingestion_service")
        self.ingestion_service = self.document_ingestion_service
        self.search_engine = SearchEngine(self.embedding_service, self.qdrant_service)
        self.query_analyzer = QueryAnalyzer()
        self.reranker = Reranker()
        self.neo4j_service = Neo4jService(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
        self.graph_builder = GraphBuilder()
        self.compliance_engine = ComplianceEngine()
        self.evidence_verifier = EvidenceVerifier()
        self.recommendation_generator = RecommendationGenerator()
        
        # Document processing utilities (for backwards compatibility and direct calls)
        self.pdf_parser = self.document_ingestion_service.pdf_parser
        self.text_extractor = self.document_ingestion_service.text_extractor
        self.chunker = self.document_ingestion_service.chunker

        # Register standard nodes in graph
        for std in self.search_engine.get_all_standards():
            self.neo4j_service.register_standard_node(std)

    def run_query_pipeline(
        self,
        query: str,
        limit: int = 5,
        document_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes critical Phase 2 retrieval flow:
        User Query -> Query Analyzer -> Query Embedding -> Qdrant Semantic Search ->
        Top-k Chunks/Standards -> Re-ranking (Weighted Heuristic) ->
        Evidence Verification (Page & Clause) -> Knowledge Graph Links ->
        Recommendation Generator -> Structured JSON.
        """
        recommendation_id = f"rec_{uuid.uuid4().hex[:8]}"

        # Stage 1: Query Understanding
        query_analysis = self.query_analyzer.analyze(query)
        if query_analysis.get("is_empty"):
            return {
                "recommendation_id": recommendation_id,
                "query": query,
                "total_recommendations": 0,
                "recommendations": [],
                "query_analysis": query_analysis,
                "data_mode": "DEMO",
                "retrieval_mode": self.qdrant_service.retrieval_mode,
                "embedding_mode": self.embedding_service.provider_name,
                "error": "Empty query provided"
            }

        # Multilingual Response Language resolution
        response_lang = query_analysis.get("response_language") or query_analysis.get("detected_language") or "en"
        response_lang_name = query_analysis.get("response_language_name", "English")

        # Multilingual Handling (Feature M9):
        # If non-English query normalization is marked INCOMPLETE, do not invent standards
        if query_analysis.get("normalization_status") == "INCOMPLETE":
            from ai_engine.recommendation.multilingual_response import MultilingualResponseGenerator
            incomplete_msg = MultilingualResponseGenerator.format_incomplete_normalization_message(response_lang)
            return {
                "recommendation_id": recommendation_id,
                "query": query,
                "total_recommendations": 0,
                "recommendations": [],
                "query_analysis": query_analysis,
                "data_mode": "VERIFIED_SOURCE",
                "retrieval_mode": self.qdrant_service.retrieval_mode,
                "embedding_mode": self.embedding_service.provider_name,
                "message": incomplete_msg,
                "response_language": response_lang,
                "response_language_name": response_lang_name
            }

        # Use normalized English query for semantic retrieval if translation occurred
        search_query = query_analysis.get("normalized_english_query") or query

        # Stage 2: Document / Standards Semantic Search via Vector Embeddings
        retrieved_candidates = self.search_engine.retrieve(search_query, limit=limit)

        # Stage 3: Secondary Re-ranking using configurable heuristic & category compatibility
        reranked_candidates = self.reranker.rerank(search_query, retrieved_candidates, query_analysis)

        # Stage 4: Knowledge Graph Relationships, Compliance & Evidence Verification
        verified_evidence_map: Dict[str, Dict[str, Any]] = {}
        compliance_map: Dict[str, List[Dict[str, Any]]] = {}
        related_standards_map: Dict[str, List[Dict[str, Any]]] = {}

        for candidate in reranked_candidates:
            payload = candidate.get("payload", {})
            std_num = payload.get("standard_number")
            if not std_num:
                continue

            # Graph Relationships (Normative & Testing standards)
            related = self.neo4j_service.get_related_standards(std_num)
            related_standards_map[std_num] = related

            # Compliance Mandates (QCOs, ISI marks)
            compliance = self.compliance_engine.evaluate_compliance(std_num, payload.get("scope", ""))
            compliance_map[std_num] = compliance

            # Evidence Verification with Page and Clause provenance
            evidence = self.evidence_verifier.verify(payload, query, document_chunks=document_chunks)
            verified_evidence_map[std_num] = evidence

        structured_reqs = query_analysis.get("structured_requirements") or {}
        foreign_standards = structured_reqs.get("foreign_standards") or []
        prod = structured_reqs.get("product")
        add_p = structured_reqs.get("additional_parameters") or {}
        is_cable = bool(prod and ("cable" in prod or "wire" in prod)) or "cable" in query.lower() or "केबल" in query or "கேபிள்" in query

        from ai_engine.recommendation.multilingual_response import MultilingualResponseGenerator

        # Collect excluded candidates with reasons for transparency
        excluded_candidates = []
        for c in reranked_candidates:
            if c.get("voltage_incompatible") or c.get("category_incompatible") or c.get("insulation_incompatible"):
                std_p = c.get("payload", {})
                std_code = std_p.get("standard_number") or c.get("standard_number", "")
                if std_code and not any(ec["standard_number"] == std_code for ec in excluded_candidates):
                    raw_ex = c.get("exclusion_reason") or "Scope conflict with specified requirements"
                    trans_ex = MultilingualResponseGenerator.format_exclusion_reason(raw_ex, response_lang)
                    excluded_candidates.append({
                        "standard_number": std_code,
                        "title": std_p.get("title", ""),
                        "exclusion_reason": trans_ex
                    })

        # Stage 5: Recommendation Generator
        recommendations = self.recommendation_generator.build_recommendations(
            reranked_candidates=reranked_candidates,
            verified_evidence_map=verified_evidence_map,
            compliance_map=compliance_map,
            related_standards_map=related_standards_map,
            query_analysis=query_analysis
        )

        # Collect technical parameter advisories in the target response language
        advisory_notices = []
        if is_cable:
            if add_p.get("rated_voltage_volts") is None:
                advisory_notices.append(
                    "Officer verification required: Rated operating voltage was not specified in the query. "
                    "IS 694 applies up to 450/750 V; IS 1554 (Part 1) applies for heavy duty installations up to 1100 V."
                )
            if add_p.get("insulation_material") is None:
                advisory_notices.append(
                    "Officer verification required: Dielectric insulation material was not specified in the query. "
                    "IS 1554 (Part 1) covers PVC insulation; IS 7098 (Part 1) covers XLPE insulation."
                )
        advisory_notices = MultilingualResponseGenerator.format_advisory_notices(advisory_notices, response_lang)

        message = None

        # Task 2: When no adequately supported match exists, return 0 recommendations with manual review message in user's language
        if not recommendations:
            req_v = add_p.get("rated_voltage_volts")
            message = MultilingualResponseGenerator.format_limitation_message(
                response_lang=response_lang,
                product=prod,
                voltage_val=req_v,
                foreign_standards=foreign_standards,
                is_cable=is_cable
            )

            return {
                "recommendation_id": recommendation_id,
                "query": query,
                "query_analysis": query_analysis,
                "structured_requirements": structured_reqs,
                "total_recommendations": 0,
                "recommendations": [],
                "data_mode": "VERIFIED_SOURCE",
                "retrieval_mode": self.qdrant_service.retrieval_mode,
                "embedding_mode": self.embedding_service.provider_name,
                "message": message,
                "excluded_candidates": excluded_candidates,
                "advisory_notices": advisory_notices,
                "response_language": response_lang,
                "response_language_name": response_lang_name
            }

        # Task 3: If foreign standards were specified, but none of the recommended standards have a verified mapping
        if foreign_standards and not any(r.get("foreign_standard_warning") for r in recommendations):
            fs_str = ", ".join(foreign_standards)
            if response_lang == "hi":
                fs_notice = (
                    f"निविदा विदेशी मानक ({fs_str}) निर्दिष्ट करती है। अनुशंसित मानकों के लिए सक्रिय "
                    f"कैटलॉग में कोई सत्यापित समकक्ष भारतीय मानक स्थापित नहीं किया गया। अधिकारी सत्यापन आवश्यक है।"
                )
            elif response_lang == "ta":
                fs_notice = (
                    f"டெண்டர் வெளிநாட்டு தரநிலையைக் ({fs_str}) குறிப்பிடுகிறது. பரிந்துரைக்கப்பட்ட தரநிலைகளுக்கு "
                    f"செயலில் உள்ள பட்டியலில் சமமான இந்திய தரநிலை நிறுவப்படவில்லை. அதிகாரி சரிபார்ப்பு தேவைப்படுகிறது."
                )
            else:
                fs_notice = (
                    f"Tender specifies foreign standard ({fs_str}). No verified equivalent Indian Standard "
                    f"mapping was established in the active catalogue for the recommended standards. "
                    f"Manual officer verification is required to determine applicable Indian Standard equivalence."
                )
            query_analysis["foreign_standards_notice"] = fs_notice
            message = fs_notice

        # Data Mode Labeling
        is_any_demo = any(r.get("is_demo", True) for r in recommendations)
        data_mode = "DEMO" if is_any_demo else "VERIFIED_SOURCE"

        directly_applicable_count = len([
            r for r in recommendations
            if r.get("applicability_type", "DIRECTLY_APPLICABLE") == "DIRECTLY_APPLICABLE"
        ])

        summary = MultilingualResponseGenerator.format_summary(
            recommendations[0],
            response_lang,
            directly_applicable_count
        ) if recommendations else None

        return {
            "recommendation_id": recommendation_id,
            "query": query,
            "query_analysis": query_analysis,
            "structured_requirements": structured_reqs,
            "total_recommendations": directly_applicable_count,
            "recommendations": recommendations,
            "data_mode": data_mode,
            "retrieval_mode": self.qdrant_service.retrieval_mode,
            "embedding_mode": self.embedding_service.provider_name,
            "message": message,
            "excluded_candidates": excluded_candidates,
            "advisory_notices": advisory_notices,
            "response_language": response_lang,
            "response_language_name": response_lang_name,
            "summary": summary
        }

    def run_document_pipeline(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Executes document ingestion and runs retrieval over extracted specifications:
        PDF/TXT -> Parser -> Text Extraction -> Cleaning -> Chunking -> Metadata -> Embedding -> Qdrant.
        """
        # Step 1: Ingest document with full page metadata preservation
        ingest_result = self.document_ingestion_service.ingest_document(
            file_bytes=file_bytes,
            filename=filename
        )

        # Step 2: Formulate retrieval query from detected standards or extracted text
        detected = ingest_result.get("detected_explicit_standards", [])
        chunks = ingest_result.get("chunks", [])
        sample_text = " ".join([c["content"] for c in chunks[:5]])

        search_prompt = (" ".join(detected) + " " + sample_text[:1500]).strip()
        results = self.run_query_pipeline(search_prompt, limit=5, document_chunks=chunks)

        # Attach document ingestion metrics
        results["document_id"] = ingest_result.get("document_id")
        results["filename"] = filename
        results["pages_extracted"] = ingest_result.get("pages_extracted")
        results["total_chunks"] = ingest_result.get("total_chunks")
        results["detected_explicit_standards"] = detected
        return results

    def get_standard_details(self, standard_id: str) -> Dict[str, Any]:
        """Fetches standard details including related standards and graph representation."""
        std = self.search_engine.get_standard_by_id(standard_id)
        if not std:
            return {}

        std_num = std.get("standard_number", standard_id)
        related = self.neo4j_service.get_related_standards(std_num)
        compliance = self.compliance_engine.evaluate_compliance(std_num, std.get("scope", ""))
        graph_data = self.graph_builder.build_flow_graph(std, related)

        return {
            "standard": std,
            "related_standards": related,
            "compliance": compliance,
            "graph": graph_data
        }
