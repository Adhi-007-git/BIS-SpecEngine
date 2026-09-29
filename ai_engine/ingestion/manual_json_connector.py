"""
Manual JSON Ingestion Connector for SIH26108.
Loads verified standards from authoritative local catalogue file:
data/real/standards_catalogue.json
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from ai_engine.ingestion.base_connector import BaseIngestionConnector

logger = logging.getLogger("sih26108.ingestion")

class ManualJsonConnector(BaseIngestionConnector):
    """Ingestion connector reading the real 21-standard seed catalogue."""

    DEFAULT_CATALOGUE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "standards_catalogue.json"

    def __init__(self, file_path: Path = DEFAULT_CATALOGUE_PATH):
        self.file_path = file_path

    def get_source_metadata(self) -> Dict[str, Any]:
        return {
            "connector_type": "ManualJsonConnector",
            "source_path": str(self.file_path),
            "authority": "Bureau of Indian Standards",
            "dataset_version": "v1.0-real-21",
            "is_official_api": False
        }

    def fetch_standards(self) -> List[Dict[str, Any]]:
        """Reads standards catalogue file and validates every record."""
        if not self.file_path.exists():
            logger.warning(f"Standards catalogue file not found: {self.file_path}")
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_standards = json.load(f)

            valid_standards = []
            for record in raw_standards:
                if self.validate_standard_record(record):
                    valid_standards.append(record)
                else:
                    logger.warning(f"Skipping invalid standard record: {record}")

            logger.info(f"Loaded {len(valid_standards)} verified standards from {self.file_path.name}")
            return valid_standards
        except Exception as e:
            logger.error(f"Error loading standards catalogue: {e}")
            return []
