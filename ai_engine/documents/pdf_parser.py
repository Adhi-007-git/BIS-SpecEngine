"""
PDF Parser: Extracts text content on a page-by-page basis to preserve
page numbers for evidence auditing and citation.
"""
from typing import List, Dict, Any
import io

class PDFParser:
    """Extracts text per page from binary PDF streams, retaining page index and metadata."""

    def extract_pages(self, file_bytes: bytes, filename: str = "document.pdf") -> List[Dict[str, Any]]:
        """Extracts text page-by-page. Supports PDF via pypdf and plain TXT files directly."""
        pages: List[Dict[str, Any]] = []

        # 1. Plain text specification handling (.txt or non-PDF streams)
        is_txt = filename.lower().endswith(".txt") or not file_bytes.startswith(b"%PDF")
        if is_txt:
            try:
                try:
                    raw_text = file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    raw_text = file_bytes.decode('latin-1', errors='ignore')

                lines = raw_text.splitlines()
                page_size = max(40, len(lines) // 4 or 40)
                total_pages = max(1, (len(lines) + page_size - 1) // page_size)

                for page_idx in range(total_pages):
                    chunk_lines = lines[page_idx * page_size: (page_idx + 1) * page_size]
                    page_text = "\n".join(chunk_lines).strip()
                    pages.append({
                        "page_number": page_idx + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                return pages
            except Exception as exc:
                return [{
                    "page_number": 1,
                    "text": file_bytes.decode('utf-8', errors='ignore'),
                    "char_count": len(file_bytes)
                }]

        # 2. PDF extraction via pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": idx,
                    "text": text.strip(),
                    "char_count": len(text)
                })
        except Exception as e:
            # Fallback to direct string decoding if PDF reader encountered an issue
            try:
                decoded = file_bytes.decode('utf-8', errors='ignore').strip()
                if len(decoded) > 20:
                    pages.append({
                        "page_number": 1,
                        "text": decoded,
                        "char_count": len(decoded)
                    })
                    return pages
            except Exception:
                pass

            pages.append({
                "page_number": 1,
                "text": f"[Error reading PDF pages: {str(e)}]",
                "char_count": 0,
                "error": str(e)
            })

        return pages
