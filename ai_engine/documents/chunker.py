"""
Document Chunker: Segments text into contextual windows while strictly
preserving page numbers, section headers, and provenance metadata for evidence grounding.
"""
from typing import List, Dict, Any, Optional
import re

class DocumentChunker:
    """Chunks page text into overlapping windows for semantic embedding and retrieval,
    attaching complete document and page metadata to every chunk."""

    CLAUSE_PATTERN = re.compile(r'\b(Clause\s+[0-9]+(?:\.[0-9]+)*|Section\s+[0-9]+(?:\.[0-9]+)*|Part\s+[0-9]+)\b', re.IGNORECASE)

    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_pages(
        self,
        pages: List[Dict[str, Any]],
        document_id: str = "doc_1",
        filename: str = "document.pdf",
        source: str = "Uploaded Document",
        document_type: str = "tender_specification",
        standard_number: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Takes page-level extracted items and yields granular chunks with complete metadata:
        document_id, filename, page_number, section, chunk_id, source, document_type, standard_number.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 1

        for page in pages:
            page_num = page.get("page_number", 1)
            text = page.get("text", "")
            words = text.split()

            if not words:
                continue

            # Detect clause/section if present on this page
            clauses = self.CLAUSE_PATTERN.findall(text)
            detected_clause = clauses[0] if clauses else None

            # If page text is smaller than chunk size, emit single chunk
            if len(words) <= self.chunk_size:
                section_label = detected_clause or f"Page {page_num}"
                content = " ".join(words)
                chunks.append({
                    "chunk_id": f"{document_id}_p{page_num}_c{chunk_counter}",
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_num,
                    "page": page_num, # Alias for backward compatibility
                    "section": section_label,
                    "content": content,
                    "text": content, # Alias for vector payload
                    "source": source,
                    "document_type": document_type,
                    "standard_number": standard_number,
                    "token_estimate": len(words),
                    "char_count": len(content)
                })
                chunk_counter += 1
                continue

            # Sliding window over words
            start = 0
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                window_words = words[start:end]
                content = " ".join(window_words)
                
                # Check clause in window
                window_clauses = self.CLAUSE_PATTERN.findall(content)
                section_label = window_clauses[0] if window_clauses else (detected_clause or f"Page {page_num} (Passage {chunk_counter})")

                chunks.append({
                    "chunk_id": f"{document_id}_p{page_num}_c{chunk_counter}",
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_num,
                    "page": page_num,
                    "section": section_label,
                    "content": content,
                    "text": content,
                    "source": source,
                    "document_type": document_type,
                    "standard_number": standard_number,
                    "token_estimate": len(window_words),
                    "char_count": len(content)
                })
                chunk_counter += 1
                if end == len(words):
                    break
                start += (self.chunk_size - self.overlap)

        return chunks
