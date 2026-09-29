"""
Text Extractor: Sanitizes, normalizes, and identifies sections/clauses
within extracted document texts.
"""
from typing import Dict, Any, List
import re

class TextExtractor:
    """Cleans and extracts section headers, Indian Standard references, and clauses."""

    IS_PATTERN = re.compile(r'\b(IS[\s\/]*[0-9]+(?:\s*\(Part\s*[0-9]+\))?(?::[0-9]{4})?)\b', re.IGNORECASE)
    CLAUSE_PATTERN = re.compile(r'\b(Clause\s+[0-9]+(?:\.[0-9]+)*|Section\s+[0-9]+(?:\.[0-9]+)*)\b', re.IGNORECASE)

    def process_text(self, text: str) -> Dict[str, Any]:
        """Cleans whitespace, identifies IS mentions, and identifies key clauses."""
        if not text:
            return {"clean_text": "", "detected_standards": [], "clauses": []}

        # Normalize redundant spaces and newlines
        clean_text = re.sub(r'[ \t]+', ' ', text)
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

        # Find any explicitly mentioned Indian Standards
        standards = list(dict.fromkeys(self.IS_PATTERN.findall(clean_text)))
        clauses = list(dict.fromkeys(self.CLAUSE_PATTERN.findall(clean_text)))

        return {
            "clean_text": clean_text,
            "detected_standards": standards,
            "clauses": clauses
        }
