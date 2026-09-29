"""
Base Ingestion Connector for SIH26108.
Defines abstract interface for ingesting Indian Standards catalogues from
manual JSON seeds or future official authenticated BIS data feeds.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseIngestionConnector(ABC):
    """Abstract connector interface for standards data ingestion."""

    @abstractmethod
    def fetch_standards(self) -> List[Dict[str, Any]]:
        """Retrieves verified standard records from the source."""
        pass

    @abstractmethod
    def get_source_metadata(self) -> Dict[str, Any]:
        """Returns provenance and connection metadata for audit tracking."""
        pass

    def validate_standard_record(self, record: Dict[str, Any]) -> bool:
        """Validates that a standard record has non-empty standard_number and title."""
        if not isinstance(record, dict):
            return False
        num = record.get("standard_number")
        title = record.get("title")
        return bool(num and str(num).strip() and title and str(title).strip())
