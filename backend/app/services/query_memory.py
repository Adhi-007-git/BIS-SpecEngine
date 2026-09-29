"""
Query Memory Service for SIH26108.
Searches historical engineer-approved knowledge to accelerate answers while
verifying live standard status to prevent using stale or superseded standards.
NOTE: Never retrains or fine-tunes the LLM from memory.
"""
from typing import Dict, Any, List, Optional
import re
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.core.database import SessionLocal
from backend.app.models.entities import VerifiedAnswer, Standard, StandardVersionHistory

logger = logging.getLogger("sih26108.query_memory")

class QueryMemoryService:
    """Manages persistent query memory matching against engineer-approved decisions."""

    def __init__(self, db_session_factory=SessionLocal):
        self.db_session_factory = db_session_factory

    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalizes query text for deterministic indexing and similarity matching across all Unicode scripts."""
        if not query:
            return ""
        import unicodedata
        # Unicode-safe cleaning: preserve letters (any script), combining marks (matras/viramas), numbers, hyphens
        def is_valid_char(c: str) -> bool:
            cat = unicodedata.category(c)
            return cat.startswith(('L', 'M', 'N')) or c in '-_/'

        cleaned = "".join(c if is_valid_char(c) else " " for c in query.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 1]
        return " ".join(tokens)

    def verify_current_status(self, standard_number: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Verifies the live catalog status of a standard:
        Checks if active, superseded, or withdrawn.
        """
        should_close = False
        if db is None:
            db = self.db_session_factory()
            should_close = True

        try:
            # Check version history first for recent changes
            history = db.query(StandardVersionHistory).filter(
                (StandardVersionHistory.standard_number == standard_number) |
                (StandardVersionHistory.previous_version == standard_number)
            ).order_by(StandardVersionHistory.change_date.desc()).first()

            if history and history.status.lower() in ("superseded", "withdrawn"):
                return {
                    "standard_number": standard_number,
                    "is_active": False,
                    "is_superseded": True,
                    "status": history.status,
                    "superseded_by": history.new_version,
                    "warning": f"Standard '{standard_number}' was superseded by '{history.new_version}' on {history.change_date.strftime('%Y-%m-%d')}."
                }

            # Check standards table if available
            std = db.query(Standard).filter(Standard.standard_number == standard_number).first()
            if std:
                is_active = std.status.lower() == "active"
                return {
                    "standard_number": standard_number,
                    "is_active": is_active,
                    "is_superseded": not is_active,
                    "status": std.status,
                    "superseded_by": None,
                    "warning": None if is_active else f"Standard '{standard_number}' status is {std.status}."
                }

            # Default: Standard is assumed active if no negative record exists
            return {
                "standard_number": standard_number,
                "is_active": True,
                "is_superseded": False,
                "status": "Active",
                "superseded_by": None,
                "warning": None
            }
        finally:
            if should_close:
                db.close()

    def find_memory_match(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Searches previous APPROVED or MODIFIED verified answers for a matching query.
        Excludes REJECTED and PENDING answers.
        Verifies live standard status before returning.
        """
        if not query or not query.strip():
            return None

        norm_query = self.normalize_query(query)
        if not norm_query:
            return None

        query_tokens = set(norm_query.split())
        db = self.db_session_factory()

        try:
            # Fetch all engineer approved or modified records
            records = db.query(VerifiedAnswer).filter(
                VerifiedAnswer.engineer_status.in_(["APPROVED", "MODIFIED"])
            ).all()

            best_match: Optional[VerifiedAnswer] = None
            highest_overlap = 0.0

            for rec in records:
                rec_norm = rec.normalized_query or self.normalize_query(rec.original_query)
                rec_tokens = set(rec_norm.split())

                if not rec_tokens:
                    continue

                # Exact match
                if norm_query == rec_norm:
                    best_match = rec
                    highest_overlap = 1.0
                    break

                # Substring containment
                if norm_query in rec_norm or rec_norm in norm_query:
                    best_match = rec
                    highest_overlap = 0.95
                    break

                # Jaccard token overlap
                intersection = query_tokens.intersection(rec_tokens)
                union = query_tokens.union(rec_tokens)
                if union:
                    jaccard = len(intersection) / len(union)
                    if jaccard > 0.4 and jaccard > highest_overlap:
                        highest_overlap = jaccard
                        best_match = rec

            if not best_match:
                return None

            # Verify live standard status
            status_check = self.verify_current_status(best_match.primary_standard, db=db)

            return {
                "verified_answer_id": best_match.id,
                "recommendation_id": best_match.recommendation_id,
                "original_query": best_match.original_query,
                "primary_standard": best_match.primary_standard,
                "related_standards": best_match.related_standards or [],
                "compliance_result": best_match.compliance_result or [],
                "evidence": best_match.evidence,
                "engineer_status": best_match.engineer_status,
                "engineer_comment": best_match.engineer_comment,
                "verified_at": best_match.verified_at.isoformat() if best_match.verified_at else None,
                "dataset_version": best_match.dataset_version,
                "status_verification": status_check,
                "is_superseded": status_check.get("is_superseded", False),
                "status_warning": status_check.get("warning")
            }
        finally:
            db.close()
