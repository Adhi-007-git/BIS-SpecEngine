"""
Phase 2 Verification Suite for SIH26108.

Tests the real retrieval pipeline additions:
  - Phase 2 response fields (retrieval_mode, embedding_mode, evidence_list, score_factors)
  - Document upload with ingestion routing
  - Backward compatibility with Phase 1 fields (evidence, page, section)
  - Health endpoint Phase 2 fields
"""
import sys
import io
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on python path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

_pass = 0
_fail = 0


def check(condition: bool, msg: str, detail: str = ""):
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  {PASS} {msg}")
    else:
        _fail += 1
        print(f"  {FAIL} {msg}" + (f": {detail}" if detail else ""))


def run_phase2_verification():
    print("=" * 62)
    print("SIH26108 Phase 2 – Retrieval Pipeline Verification")
    print("=" * 62)

    client = TestClient(app)

    # ── TEST 1: Health Check – Phase 2 Fields ─────────────────────────────
    print("\n[TEST 1] Health endpoint – Phase 2 field presence")
    resp = client.get("/api/health")
    check(resp.status_code == 200, "Health endpoint returns 200")
    data = resp.json()
    check("retrieval_mode" in data, "retrieval_mode field present in health response",
          f"keys={list(data.keys())}")
    check("embedding_mode" in data, "embedding_mode field present in health response")
    check(data.get("status") in ("ok", "healthy", "running"),
          f"Health status acceptable (got: {data.get('status')})")
    print(f"  {INFO} retrieval_mode={data.get('retrieval_mode')}  "
          f"embedding_mode={data.get('embedding_mode')}")

    # ── TEST 2: Search – Phase 2 Response Fields ───────────────────────────
    print("\n[TEST 2] Search – Phase 2 response fields")
    query = "stainless steel pipes for drinking water supply"
    resp = client.post("/api/search", json={"query": query, "limit": 3})
    check(resp.status_code == 200, "Search returns 200")
    data = resp.json()

    check("retrieval_mode" in data, "retrieval_mode field in SearchResponse",
          f"keys={list(data.keys())}")
    check("embedding_mode" in data, "embedding_mode field in SearchResponse")
    check(data.get("retrieval_mode") in ("IN_MEMORY", "QDRANT", "DEMO"),
          f"retrieval_mode has valid value (got: {data.get('retrieval_mode')})")

    recs = data.get("recommendations", [])
    check(len(recs) > 0, f"At least 1 recommendation returned (got {len(recs)})")

    if recs:
        print(f"\n[TEST 3] First recommendation – field backward compatibility")
        first = recs[0]

        # Phase 1 fields — must still exist
        check("evidence" in first and isinstance(first["evidence"], str),
              "Legacy 'evidence' field present (str)")
        check("page" in first, "Legacy 'page' field present")
        check("section" in first, "Legacy 'section' field present")
        check("standard_number" in first, "standard_number present")
        check("title" in first, "title present")
        check("relevance_score" in first, "relevance_score present")
        check("reason" in first, "reason present")
        check("source" in first, "source present")
        check("status" in first, "status present")
        check("is_demo" in first, "is_demo flag present")
        check("demo_tag" in first, "demo_tag present")

        # Phase 2 fields — optional but validated if present
        ev_list = first.get("evidence_list")
        check(ev_list is None or isinstance(ev_list, list),
              f"evidence_list is list or None (got: {type(ev_list).__name__})")

        if ev_list:
            snippet = ev_list[0]
            check("text" in snippet, "EvidenceSnippet has 'text' key")
            check("page" in snippet, "EvidenceSnippet has 'page' key")
            check("section" in snippet, "EvidenceSnippet has 'section' key")
            check("source" in snippet, "EvidenceSnippet has 'source' key")
            print(f"  {INFO} evidence_list[0].text[:60]: \"{snippet['text'][:60]}...\"")

        score_factors = first.get("score_factors")
        if score_factors:
            check(len(score_factors) > 0, "score_factors has entries")
            for k, v in score_factors.items():
                if isinstance(v, (int, float)):
                    check(0 <= v <= 1,
                          f"score_factors[{k}] in [0, 1]  (got: {v})")

        print(f"  {INFO} standard={first['standard_number']}  "
              f"score={round(first['relevance_score']*100)}%  "
              f"evidence_list_len={len(ev_list or [])}")

    # ── TEST 4: Upload – Phase 2 Response Fields ───────────────────────────
    print("\n[TEST 4] Upload – Phase 2 response fields")
    dummy_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n" \
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" \
                b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>\nendobj\n" \
                b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (IS 1239 Steel Pipes) Tj ET\nendstream\nendobj\n" \
                b"xref\n0 5\ntrailer<</Size 5/Root 1 0 R>>\nstartxref 0\n%%EOF"

    resp = client.post(
        "/api/upload",
        files={"file": ("tender_test.pdf", io.BytesIO(dummy_pdf), "application/pdf")}
    )
    check(resp.status_code == 200, f"Upload returns 200 (got: {resp.status_code})")
    if resp.status_code == 200:
        up = resp.json()
        check("document_id" in up, "document_id in UploadResponse")
        check("pages_extracted" in up, "pages_extracted in UploadResponse")
        check("total_chunks" in up, "total_chunks in UploadResponse")
        check("retrieval_mode" in up, "retrieval_mode in UploadResponse (Phase 2)")
        check("embedding_mode" in up, "embedding_mode in UploadResponse (Phase 2)")
        check("message" in up, "message field in UploadResponse")
        check("detected_explicit_standards" in up,
              "detected_explicit_standards in UploadResponse")
        print(f"  {INFO} doc_id={up.get('document_id')}  "
              f"pages={up.get('pages_extracted')}  "
              f"chunks={up.get('total_chunks')}  "
              f"retrieval={up.get('retrieval_mode')}")
    else:
        print(f"  {SKIP} Upload body: {resp.text[:200]}")

    # ── TEST 5: Recommendations – No Fabricated Standards ─────────────────
    print("\n[TEST 5] Anti-hallucination – standard numbers are plausible IS codes")
    resp = client.post("/api/search", json={"query": "cement for construction buildings", "limit": 5})
    if resp.status_code == 200:
        recs = resp.json().get("recommendations", [])
        for r in recs:
            std_num = r.get("standard_number", "")
            # All standard numbers must start with IS or BIS or similar
            check(
                std_num.startswith("IS") or std_num.startswith("BIS") or std_num.startswith("IEC"),
                f"Standard number '{std_num}' looks like a real IS/BIS/IEC code"
            )
            # Relevance score must be in valid range
            score = r.get("relevance_score", -1)
            check(0.0 <= score <= 1.0, f"Relevance score {score:.3f} in [0, 1]")

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    total = _pass + _fail
    print("\n" + "=" * 62)
    verdict = "ALL PASS" if _fail == 0 else f"{_fail} FAILED"
    print(f"Phase 2 Verification: {_pass}/{total} checks passed  [{verdict}]")
    print("=" * 62)

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_phase2_verification()
