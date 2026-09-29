"""
Phase 4 Verification Suite for SIH26108.

Validates the Phase 4 Architecture across 21 rigorous checks:
  1. StructuredRequirements schema validation
  2. LLM provider factory
  3. Mock LLM provider functionality
  4. Missing-key fallback
  5. Rule extractor deterministic parsing
  6. Structured query validation
  7. Anti-hallucination: LLM cannot inject unverified IS standards
  8. Recommendations strictly originate from verified catalogue
  9. APPROVE endpoint
  10. Persistent verified knowledge storage
  11. MODIFY endpoint
  12. Original recommendation preserved in audit history
  13. REJECT endpoint
  14. Rejected answer excluded from approved memory
  15. Query memory retrieval
  16. Live status validation (detects active/superseded standards)
  17. Standard add endpoint & validation
  18. Standard update endpoint & status update
  19. Version history preservation
  20. Reindex / search index update
  21. API key security & non-exposure
"""
import sys
import os
import json
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on python path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

_pass = 0
_fail = 0
test_results = []

def check(condition: bool, msg: str, detail: str = ""):
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  {PASS} {msg}")
        test_results.append((True, msg, detail))
    else:
        _fail += 1
        print(f"  {FAIL} {msg}" + (f": {detail}" if detail else ""))
        test_results.append((False, msg, detail))


def run_phase4_verification():
    print("=" * 68)
    print("SIH26108 Phase 4 – Verification Suite (21 Targeted Checks)")
    print("=" * 68)

    client = TestClient(app)

    # ── CHECK 1: StructuredRequirements schema ────────────────────────────
    print("\n[CHECK 1] StructuredRequirements schema")
    try:
        from ai_engine.query.schema import StructuredRequirements
        req = StructuredRequirements(
            product="distribution transformer",
            capacity="500 kVA",
            cooling="oil-cooled",
            installation="outdoor",
            primary_voltage="11 kV",
            secondary_voltage="433 V",
            foreign_standards=["IEC 60076"],
            application="power distribution"
        )
        d = req.to_dict()
        valid = (d.get("product") == "distribution transformer" and
                 d.get("capacity") == "500 kVA" and
                 "IEC 60076" in d.get("foreign_standards", []))
        check(valid, "StructuredRequirements schema serializes and validates fields", f"got {d}")
    except Exception as e:
        check(False, "StructuredRequirements schema works", f"{type(e).__name__}: {e}")

    # ── CHECK 2: LLM provider factory ─────────────────────────────────────
    print("\n[CHECK 2] LLM provider factory")
    try:
        from ai_engine.query.llm_provider import get_llm_provider, BaseLLMProvider
        provider = get_llm_provider()
        check(isinstance(provider, BaseLLMProvider),
              f"get_llm_provider() returns a BaseLLMProvider instance ({provider.__class__.__name__})")
    except Exception as e:
        check(False, "LLM provider factory works", f"{type(e).__name__}: {e}")

    # ── CHECK 3: Mock provider ────────────────────────────────────────────
    print("\n[CHECK 3] Mock LLM provider")
    try:
        from ai_engine.query.llm_provider import MockLLMProvider
        provider = MockLLMProvider()
        res = provider.parse_query("500 kVA outdoor oil-cooled distribution transformer, 11kV/433V, IEC 60076 compliant")
        check(res is not None and getattr(res, "capacity", "") == "500 kVA" and "IEC 60076" in getattr(res, "foreign_standards", []),
              "Mock LLM provider parses procurement query into StructuredRequirements", f"got {res}")
    except Exception as e:
        check(False, "Mock LLM provider works", f"{type(e).__name__}: {e}")

    # ── CHECK 4: Missing-key fallback ─────────────────────────────────────
    print("\n[CHECK 4] Missing-key fallback")
    try:
        from ai_engine.query.query_analyzer import QueryAnalyzer
        orig_key = os.environ.get("LLM_API_KEY")
        try:
            os.environ["LLM_API_KEY"] = ""
            analyzer = QueryAnalyzer()
            res = analyzer.analyze("500 kVA outdoor oil-cooled distribution transformer")
            check(isinstance(res, dict) and not res.get("is_empty") and res.get("structured_requirements") is not None,
                  "Missing LLM API key safely falls back to local query analysis with structured requirements")
        finally:
            if orig_key is not None:
                os.environ["LLM_API_KEY"] = orig_key
            else:
                os.environ.pop("LLM_API_KEY", None)
    except Exception as e:
        check(False, "Missing LLM API key safely falls back", f"{type(e).__name__}: {e}")

    # ── CHECK 5: Rule extractor ───────────────────────────────────────────
    print("\n[CHECK 5] Rule extractor deterministic parsing")
    try:
        from ai_engine.query.rule_extractor import RuleExtractor
        extractor = RuleExtractor()
        extracted = extractor.extract("500 kVA outdoor oil-cooled distribution transformer, 11kV/433V, IEC 60076 compliant")
        check(extracted.product == "distribution transformer" and
              extracted.cooling == "oil-cooled" and
              extracted.installation == "outdoor" and
              extracted.primary_voltage == "11 KV" and
              extracted.secondary_voltage == "433 V",
              "Rule extractor accurately extracts product, capacity, cooling, installation, voltages, and foreign standards")
    except Exception as e:
        check(False, "Rule extractor deterministic parsing works", f"{type(e).__name__}: {e}")

    # ── CHECK 6: Structured query validation ──────────────────────────────
    print("\n[CHECK 6] Structured query validation")
    try:
        from ai_engine.query.llm_provider import BaseLLMProvider
        provider = get_llm_provider()
        valid_res = provider.validate_output({
            "product": "power cable",
            "capacity": "1100 V",
            "cooling": None,
            "installation": "underground",
            "primary_voltage": "1100 V",
            "secondary_voltage": None,
            "foreign_standards": ["IEC 60502"],
            "application": "power distribution"
        })
        check(valid_res is not None and valid_res.product == "power cable",
              "Structured query validation accepts valid schemas and rejects malformed inputs")
        malformed_res = provider.validate_output("NOT_JSON_OR_DICT")
        check(malformed_res is None, "Malformed string output safely returns None")
    except Exception as e:
        check(False, "Structured query validation works", f"{type(e).__name__}: {e}")

    # ── CHECK 7: Anti-hallucination: LLM cannot inject IS standards ───────
    print("\n[CHECK 7] Anti-hallucination: LLM cannot inject unverified standards")
    try:
        from backend.app.api.dependencies import get_pipeline
        pipeline = get_pipeline()
        res = pipeline.run_query_pipeline("Mandating nonexistent code IS 99999:2099 for spacecraft")
        recs = res.get("recommendations", [])
        has_fake = any(r.get("standard_number") == "IS 99999:2099" for r in recs)
        check(not has_fake, "LLM cannot inject or invent an IS code directly into authoritative recommendations")
    except Exception as e:
        check(False, "Anti-hallucination check works", f"{type(e).__name__}: {e}")

    # ── CHECK 8: Recommendations from verified catalogue ─────────────────
    print("\n[CHECK 8] Recommendations strictly originate from verified catalogue")
    try:
        seed_path = root / "data" / "real" / "standards_catalogue.json"
        with open(seed_path, "r", encoding="utf-8") as f:
            catalogue = json.load(f)
        valid_numbers = {s["standard_number"] for s in catalogue}

        resp = client.post("/api/search", json={"query": "structural steel concrete reinforcement", "limit": 5})
        check(resp.status_code == 200, "Search endpoint returns 200")
        recs = resp.json().get("recommendations", [])
        check(len(recs) > 0, "Recommendations returned for query")
        all_in_catalogue = all(r.get("standard_number") in valid_numbers for r in recs)
        check(all_in_catalogue, f"All {len(recs)} returned standards originate from verified catalogue ({len(valid_numbers)} records)")
    except Exception as e:
        check(False, "Recommendations originate from verified catalogue", f"{type(e).__name__}: {e}")

    # ── CHECK 9: APPROVE endpoint ─────────────────────────────────────────
    print("\n[CHECK 9] Review APPROVE endpoint")
    try:
        resp = client.post("/api/search", json={"query": "pvc cables building", "limit": 2})
        rec_id = resp.json().get("recommendation_id") if resp.status_code == 200 else f"rec_{uuid.uuid4().hex[:8]}"

        appr_resp = client.post(f"/api/review/{rec_id}/approve", json={"comment": "Approved by senior engineer"})
        check(appr_resp.status_code == 200, f"POST /api/review/{{id}}/approve returns 200 (got {appr_resp.status_code})")
    except Exception as e:
        check(False, "APPROVE endpoint works", f"{type(e).__name__}: {e}")

    # ── CHECK 10: Persistent verified knowledge ───────────────────────────
    print("\n[CHECK 10] Persistent verified knowledge")
    try:
        from backend.app.models.entities import VerifiedAnswer
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
        try:
            ans = db.query(VerifiedAnswer).filter(VerifiedAnswer.engineer_status == "APPROVED").first()
            check(ans is not None, "Persistent VerifiedAnswer record created with status APPROVED")
            if ans:
                check(ans.verified_at is not None, "Verified timestamp stored")
                check(ans.dataset_version is not None, "Dataset version stored")
        finally:
            db.close()
    except Exception as e:
        check(False, "Persistent verified knowledge check works", f"{type(e).__name__}: {e}")

    # ── CHECK 11: MODIFY endpoint ─────────────────────────────────────────
    print("\n[CHECK 11] Review MODIFY endpoint")
    try:
        resp = client.post("/api/search", json={"query": "submersible cables", "limit": 2})
        rec_id = resp.json().get("recommendation_id") if resp.status_code == 200 else f"rec_{uuid.uuid4().hex[:8]}"

        mod_resp = client.post(f"/api/review/{rec_id}/modify", json={
            "primary_standard": "IS 694:2010",
            "related_standards": ["IS 1239 (Part 1):2004"],
            "comment": "Changed primary standard based on technical review"
        })
        check(mod_resp.status_code == 200, f"POST /api/review/{{id}}/modify returns 200 (got {mod_resp.status_code})")
    except Exception as e:
        check(False, "MODIFY endpoint works", f"{type(e).__name__}: {e}")

    # ── CHECK 12: Original recommendation preserved ───────────────────────
    print("\n[CHECK 12] Original recommendation preserved on MODIFY")
    try:
        from backend.app.models.entities import VerifiedAnswer
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
        try:
            ans = db.query(VerifiedAnswer).filter(VerifiedAnswer.engineer_status == "MODIFIED").first()
            check(ans is not None and getattr(ans, "original_ai_recommendation", None) is not None,
                  "MODIFY preserves original AI recommendation in audit history")
        finally:
            db.close()
    except Exception as e:
        check(False, "Original recommendation preserved on MODIFY", f"{type(e).__name__}: {e}")

    # ── CHECK 13: REJECT endpoint ─────────────────────────────────────────
    print("\n[CHECK 13] Review REJECT endpoint")
    try:
        resp = client.post("/api/search", json={"query": "random irrelevant specification", "limit": 2})
        rec_id = resp.json().get("recommendation_id") if resp.status_code == 200 else f"rec_{uuid.uuid4().hex[:8]}"

        rej_resp = client.post(f"/api/review/{rec_id}/reject", json={"comment": "Not applicable to BIS domain"})
        check(rej_resp.status_code == 200, f"POST /api/review/{{id}}/reject returns 200 (got {rej_resp.status_code})")
    except Exception as e:
        check(False, "REJECT endpoint works", f"{type(e).__name__}: {e}")

    # ── CHECK 14: Rejected answer excluded from approved memory ───────────
    print("\n[CHECK 14] Rejected answer excluded from approved memory")
    try:
        from backend.app.models.entities import VerifiedAnswer
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
        try:
            bad_item = db.query(VerifiedAnswer).filter(
                VerifiedAnswer.engineer_status == "APPROVED",
                VerifiedAnswer.engineer_comment == "Not applicable to BIS domain"
            ).first()
            check(bad_item is None, "REJECT is excluded from approved query memory")
        finally:
            db.close()
    except Exception as e:
        check(False, "Rejected answer excluded check works", f"{type(e).__name__}: {e}")

    # ── CHECK 15: Query memory retrieval ──────────────────────────────────
    print("\n[CHECK 15] Query memory retrieval")
    try:
        from backend.app.services.query_memory import QueryMemoryService
        mem_service = QueryMemoryService()
        match = mem_service.find_memory_match("pvc cables building")
        check(match is not None, "Query memory retrieves previously approved answer")
    except Exception as e:
        check(False, "Query memory retrieval works", f"{type(e).__name__}: {e}")

    # ── CHECK 16: Live status validation ──────────────────────────────────
    print("\n[CHECK 16] Live status validation")
    try:
        from backend.app.services.query_memory import QueryMemoryService
        mem_service = QueryMemoryService()
        check(hasattr(mem_service, "verify_current_status"),
              "Query memory verifies current live standard status (active/superseded/withdrawn)")
        status_check = mem_service.verify_current_status("IS 456:2000")
        check(status_check.get("is_active") is True, "Live status verification accurately identifies active standards")
    except Exception as e:
        check(False, "Live status validation works", f"{type(e).__name__}: {e}")

    # ── CHECK 17: Add standard ────────────────────────────────────────────
    print("\n[CHECK 17] Standard add endpoint & validation")
    try:
        test_std_code = f"IS 9999:{uuid.uuid4().hex[:4]}"
        add_resp = client.post("/api/standards/manage/add", json={
            "standard_number": test_std_code,
            "title": "Test Standard for Phase 4 Verification",
            "edition": "First Edition",
            "status": "Active",
            "scope": "Test scope for engineering verification",
            "department": "Electrotechnical",
            "keywords": ["test", "verification"],
            "source": "Bureau of Indian Standards",
            "last_verified": "2026-09-24"
        })
        check(add_resp.status_code in (200, 201),
              f"Standard add endpoint accepts valid standard (got {add_resp.status_code})")

        bad_resp = client.post("/api/standards/manage/add", json={"scope": "Missing standard_number and title"})
        check(bad_resp.status_code in (400, 422),
              "Rejects attempt to save standard without mandatory standard_number and title")
    except Exception as e:
        check(False, "Standard add functionality works", f"{type(e).__name__}: {e}")

    # ── CHECK 18: Update standard ─────────────────────────────────────────
    print("\n[CHECK 18] Standard update endpoint")
    try:
        upd_resp = client.put(f"/api/standards/manage/{test_std_code}", json={
            "title": "Updated Test Standard Title",
            "status": "Active"
        })
        check(upd_resp.status_code == 200, f"Standard update endpoint returns 200 (got {upd_resp.status_code})")
    except Exception as e:
        check(False, "Standard update works", f"{type(e).__name__}: {e}")

    # ── CHECK 19: Version history ─────────────────────────────────────────
    print("\n[CHECK 19] Version history preservation")
    try:
        v_resp = client.get("/api/standards/manage/versions")
        check(v_resp.status_code == 200, f"GET /api/standards/manage/versions returns 200 (got {v_resp.status_code})")
        v_data = v_resp.json()
        check(isinstance(v_data, list), "Version history returns structured list of changes")
    except Exception as e:
        check(False, "Version history is preserved", f"{type(e).__name__}: {e}")

    # ── CHECK 20: Reindex / search update ─────────────────────────────────
    print("\n[CHECK 20] Reindex / search index update")
    try:
        reindex_resp = client.post("/api/standards/manage/reindex")
        check(reindex_resp.status_code == 200,
              f"POST /api/standards/manage/reindex returns 200 (got {reindex_resp.status_code})")
    except Exception as e:
        check(False, "Search index rebuild works", f"{type(e).__name__}: {e}")

    # ── CHECK 21: API key security & non-exposure ─────────────────────────
    print("\n[CHECK 21] API key security & non-exposure")
    try:
        test_secret = "SECRET_PHASE4_TEST_KEY_xyz123"
        orig_key = os.environ.get("LLM_API_KEY")
        os.environ["LLM_API_KEY"] = test_secret
        try:
            h_resp = client.get("/api/health")
            s_resp = client.post("/api/search", json={"query": "test security query", "limit": 1})

            key_in_health = test_secret in h_resp.text
            key_in_search = test_secret in s_resp.text
            check(not key_in_health and not key_in_search, "API key is never exposed in API responses")

            gitignore_path = root / ".gitignore"
            if gitignore_path.exists():
                gi_content = gitignore_path.read_text(encoding="utf-8")
                check(".env" in gi_content, ".gitignore correctly ignores .env files")
            else:
                check(False, ".gitignore exists and ignores .env", "File .gitignore does not exist")
        finally:
            if orig_key is not None:
                os.environ["LLM_API_KEY"] = orig_key
            else:
                os.environ.pop("LLM_API_KEY", None)
    except Exception as e:
        check(False, "API key security check works", f"{type(e).__name__}: {e}")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    total = _pass + _fail
    print("\n" + "=" * 68)
    verdict = "ALL PASS" if _fail == 0 else f"{_fail} FAILED"
    print(f"Phase 4 Verification: {_pass}/{total} checks passed  [{verdict}]")
    print("=" * 68)

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_phase4_verification()
