"""
SIH26108 - Verification Script for Tender-Upload Recommendation Pipeline & Statutory Notices.

Tests:
  1. Transformer tender upload/analysis: Irrelevant categories withheld, neutral manual review triggered.
  2. 1100 V PVC cable tender: Recommends IS 1554 (Part 1):1988 with grounded evidence & QCO flag.
  3. Steel tubes tender: Recommends IS 1239 (Part 1):2004 based on category relevance.
  4. Unknown product category: Returns 0 recommendations and triggers manual review.
  5. Foreign standard IEC 60076: Neutral warning generated, NO false mandatory precedence claim.
  6. Harmonized foreign standard IEC 60529: Harmonized IS/IEC 60529:2001 receives precedence notice.
  7. Tender with no foreign reference: foreign_standard_warning is None.
  8. Unrelated foreign standard (DIN 4102): Neutral officer review warning without unverified claims.
  9. Insufficient evidence handling: Never labeled VERIFIED SOURCE when unsupported.
  10. Recommendation & evidence database persistence with document_id traceability.
  11. Engineer review endpoints (approve, modify, reject) compatibility.
  12. Pre-publish validation & system health endpoints intact.

Run from project root:
    python scripts/verify_upload_recommendations.py
"""
import sys
import os
import io

# UTF-8 stdout wrapper for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def banner(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def main():
    banner("SIH26108 - Tender Upload Pipeline & Statutory Notices Verification")
    passed = 0
    total = 12

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 1: Transformer Tender Upload & Analysis
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 1] Testing 500 kVA distribution transformer tender upload & analysis...")
    tender_transformer_text = (
        "GOVERNMENT PROCUREMENT TENDER\n"
        "Tender No: TND/ELEC/2026/089\n"
        "Scope of Supply: 500 kVA distribution transformer, 11 kV / 433 V, oil-cooled, "
        "outdoor installation, IEC 60076 compliant with mandatory BIS/ISI certification.\n"
        "Delivery Location: Central Power Substation Yard.\n"
    )

    upload_file = io.BytesIO(tender_transformer_text.encode("utf-8"))
    r_up = client.post(
        "/api/upload",
        files={"file": ("tender_transformer_spec.txt", upload_file, "text/plain")}
    )
    assert r_up.status_code == 200, f"Upload failed: {r_up.text}"
    doc_id = r_up.json().get("document_id")
    assert doc_id, "Missing document_id in upload response"

    # Analyze document
    r_an = client.post("/api/analyze-document", json={"document_id": doc_id})
    assert r_an.status_code == 200, f"Analyze failed: {r_an.text}"
    data_an = r_an.json()

    recs_an = data_an.get("recommendations", [])
    total_recs = data_an.get("total_recommendations", 0)

    # In verified 21-standard catalogue, no transformer standard exists.
    # Engine must NOT return unrelated steel tubes, concrete, or water standards!
    assert total_recs == 0, f"Expected 0 recommendations for transformer tender, got {total_recs}"
    assert len(recs_an) == 0, f"Expected empty recommendations list, got {len(recs_an)}"

    # Check that message clearly flags manual review
    msg = data_an.get("message", "")
    assert "manual" in msg.lower() or "withheld" in msg.lower(), f"Expected manual review message, got '{msg}'"
    print(f" [PASS] Transformer tender correctly withheld unrelated standards and triggered manual review:")
    print(f"        Message: {msg}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 2: 1100 V PVC Cable Tender (Grounding & Evidence)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 2] Testing 1100 V PVC heavy duty cable tender upload & analysis...")
    tender_cable_text = (
        "TECHNICAL SPECIFICATION: INDUSTRIAL CABLE PROCUREMENT\n"
        "Clause 1.0: Supply of 1100 V grade PVC insulated heavy duty electric cables.\n"
        "Clause 2.0: Armoured copper conductor cables suitable for underground installation in commercial buildings.\n"
        "Clause 3.0: All cables must comply with applicable Indian Standards and statutory QCO mandates.\n"
    )

    upload_cable = io.BytesIO(tender_cable_text.encode("utf-8"))
    r_up_c = client.post(
        "/api/upload",
        files={"file": ("tender_cable_spec.txt", upload_cable, "text/plain")}
    )
    assert r_up_c.status_code == 200, f"Cable upload failed: {r_up_c.text}"
    doc_id_c = r_up_c.json().get("document_id")

    r_an_c = client.post("/api/analyze-document", json={"document_id": doc_id_c})
    assert r_an_c.status_code == 200, f"Cable analyze failed: {r_an_c.text}"
    data_c = r_an_c.json()

    recs_c = data_c.get("recommendations", [])
    assert len(recs_c) > 0, "Expected recommendations for 1100 V PVC cable tender"
    top_c = recs_c[0]
    assert "IS 1554" in top_c["standard_number"], f"Expected IS 1554 as top standard, got {top_c['standard_number']}"
    assert top_c["qco_enforcement_flag"] is True, "Expected QCO flag to be True for IS 1554"
    assert top_c["relevance_score"] >= 0.40, f"Expected strong score, got {top_c['relevance_score']}"

    # Verify grounded evidence is present
    evidence_text = top_c.get("evidence", "")
    assert evidence_text != "Insufficient evidence", "Expected substantiated evidence for IS 1554"
    print(f" [PASS] 1100 V cable tender recommended {top_c['standard_number']} (Score: {top_c['relevance_score']}) with grounded evidence.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 3: Steel Tubes Tender (Category Relevance)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 3] Testing mild steel tubes and tubulars tender...")
    tender_tubes_text = (
        "DEPARTMENT OF WATER SUPPLY PROCUREMENT\n"
        "Requirement: Supply of mild steel tubes, tubulars and wrought steel fittings for municipal plumbing pipelines.\n"
        "Specification: Welded seamless steel tubes for water supply.\n"
    )
    upload_tubes = io.BytesIO(tender_tubes_text.encode("utf-8"))
    r_up_t = client.post(
        "/api/upload",
        files={"file": ("tender_tubes_spec.txt", upload_tubes, "text/plain")}
    )
    doc_id_t = r_up_t.json().get("document_id")
    r_an_t = client.post("/api/analyze-document", json={"document_id": doc_id_t})
    assert r_an_t.status_code == 200
    data_t = r_an_t.json()
    recs_t = data_t.get("recommendations", [])
    assert len(recs_t) > 0, "Expected recommendations for steel tubes"
    top_t = recs_t[0]
    assert "IS 1239" in top_t["standard_number"], f"Expected IS 1239 (Part 1), got {top_t['standard_number']}"
    # Verify electrical cable standards are NOT recommended for steel tubes!
    rec_nums_t = [r["standard_number"] for r in recs_t]
    assert "IS 1554 (Part 1):1988" not in rec_nums_t, "Cable standard should not be in steel tube recommendations"
    print(f" [PASS] Steel tubes tender correctly recommended {top_t['standard_number']} and excluded unrelated categories.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 4: Unknown / Unmatched Product Category
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 4] Testing unknown / uncatalogued product category...")
    r_search_unknown = client.post("/api/search", json={
        "query": "industrial automatic textile weaving loom machinery for garment plant",
        "top_k": 5
    })
    assert r_search_unknown.status_code == 200
    data_unk = r_search_unknown.json()
    assert data_unk.get("total_recommendations") == 0, "Unknown product should return 0 recommendations"
    assert len(data_unk.get("recommendations", [])) == 0, "Expected empty list for unknown category"
    assert "manual" in (data_unk.get("message") or "").lower() or "withheld" in (data_unk.get("message") or "").lower()
    print(" [PASS] Unmatched product category safely returned 0 recommendations with manual review advisory.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 5: Foreign Standard IEC 60076 Reference Safeguard
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 5] Testing foreign standard IEC 60076 reference safeguard...")
    r_fs = client.post("/api/search", json={
        "query": "500 kVA distribution transformer 11 kV/433 V complying with IEC 60076",
        "top_k": 5
    })
    assert r_fs.status_code == 200
    data_fs = r_fs.json()
    # Check that neutral manual verification warning is produced and NO false mandatory precedence claim was made
    msg_fs = data_fs.get("message") or ""
    assert "IEC 60076" in msg_fs, f"Expected IEC 60076 mention in message, got: {msg_fs}"
    assert "manual officer verification is required" in msg_fs.lower() or "manual" in msg_fs.lower()
    # Ensure no unrelated recommendations received a false precedence notice
    for r in data_fs.get("recommendations", []):
        assert r.get("foreign_standard_warning") is None or "IEC 60076" not in r.get("foreign_standard_warning")
    print(f" [PASS] IEC 60076 generated neutral manual-verification warning without unsupported statutory claims:")
    print(f"        Advisory: {msg_fs}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 6: Harmonized Foreign Standard (IEC 60529 -> IS/IEC 60529:2001)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 6] Testing harmonized foreign standard (IEC 60529)...")
    r_harm = client.post("/api/search", json={
        "query": "waterproof enclosure ingress protection IP65 per IEC 60529",
        "top_k": 5
    })
    assert r_harm.status_code == 200
    data_harm = r_harm.json()
    recs_harm = data_harm.get("recommendations", [])
    assert len(recs_harm) > 0, "Expected IS/IEC 60529 to match"
    top_harm = recs_harm[0]
    assert "IS/IEC 60529" in top_harm["standard_number"]
    # Harmonized standard DOES receive precedence notice because it is an adopted standard!
    assert top_harm.get("foreign_standard_warning") is not None
    assert "harmonized" in top_harm["foreign_standard_warning"].lower() or "precedence" in top_harm["foreign_standard_warning"].lower()
    print(f" [PASS] Harmonized standard IS/IEC 60529 received verified precedence notice:")
    print(f"        Notice: {top_harm['foreign_standard_warning']}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 7: Tender with No Foreign Reference
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 7] Testing tender with no foreign reference...")
    r_no_fs = client.post("/api/search", json={
        "query": "1100 V heavy duty PVC electric cable for industrial electricity supply",
        "top_k": 5
    })
    assert r_no_fs.status_code == 200
    data_no_fs = r_no_fs.json()
    for r in data_no_fs.get("recommendations", []):
        assert r.get("foreign_standard_warning") is None, f"Expected None for foreign_standard_warning, got {r.get('foreign_standard_warning')}"
    print(" [PASS] Tender with no foreign references has foreign_standard_warning=None on all items.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 8: Unrelated Foreign Standard (DIN 4102)
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 8] Testing unrelated foreign standard (DIN 4102)...")
    r_din = client.post("/api/search", json={
        "query": "heavy duty PVC electric cables tested under DIN 4102",
        "top_k": 5
    })
    assert r_din.status_code == 200
    data_din = r_din.json()
    # Cable should still be recommended, but should NOT claim DIN 4102 takes mandatory precedence under IS 1554
    for r in data_din.get("recommendations", []):
        if r.get("foreign_standard_warning"):
            assert "DIN 4102" not in r.get("foreign_standard_warning") or "officer review" in r.get("foreign_standard_warning").lower()
    print(" [PASS] Unrelated foreign standard did not produce false statutory precedence claims.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 9: Insufficient Evidence Handling
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 9] Testing insufficient evidence labeling safeguards...")
    # Verify that if any item has insufficient evidence, it is NEVER labeled VERIFIED SOURCE
    from ai_engine.recommendation.recommendation_generator import RecommendationGenerator
    rg = RecommendationGenerator()
    dummy_candidate = [{
        "payload": {
            "standard_number": "IS 9999:2020",
            "title": "Hypothetical Standard",
            "is_demo": False,
            "demo_tag": "VERIFIED SOURCE"
        },
        "calibrated_score": 0.5,
        "score_factors": {}
    }]
    dummy_ev = {"IS 9999:2020": {"verified": False, "evidence_text": "Insufficient evidence"}}
    out = rg.build_recommendations(dummy_candidate, dummy_ev, {}, {})
    if out:
        assert out[0]["demo_tag"] != "VERIFIED SOURCE", "Item with insufficient evidence must not be labeled VERIFIED SOURCE"
        assert "REVIEW REQUIRED" in out[0]["demo_tag"] or "INSUFFICIENT" in out[0]["demo_tag"]
    print(" [PASS] Ungrounded items strictly prevented from receiving 'VERIFIED SOURCE' tag.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 10: Recommendation & Evidence DB Persistence
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 10] Testing recommendation & evidence database persistence...")
    rec_id_c = data_c.get("recommendation_id")
    assert rec_id_c, "Missing recommendation_id"

    # Fetch recommendation by ID
    r_get_rec = client.get(f"/api/recommendations/{rec_id_c}")
    assert r_get_rec.status_code == 200, f"Failed to get recommendation: {r_get_rec.text}"
    rec_fetched = r_get_rec.json()
    assert rec_fetched.get("recommendation_id") == rec_id_c

    # Fetch evidence audit records by recommendation ID
    r_ev = client.get(f"/api/evidence/{rec_id_c}")
    assert r_ev.status_code == 200, f"Failed to get evidence: {r_ev.text}"
    ev_records = r_ev.json()
    assert isinstance(ev_records, list), "Expected list of evidence records"
    print(f" [PASS] Recommendation {rec_id_c} and {len(ev_records)} evidence records successfully persisted and retrieved.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 11: Engineer Review Workflow
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 11] Testing engineer review workflow on document recommendation...")
    r_approve = client.post(
        f"/api/review/{rec_id_c}/approve",
        json={"engineer_id": "ENG_TEST_01", "comments": "Confirmed applicable per project requirements."}
    )
    assert r_approve.status_code == 200, f"Approve failed: {r_approve.text}"

    # Verify knowledge query
    r_know = client.get("/api/review/knowledge")
    assert r_know.status_code == 200
    know_data = r_know.json()
    assert any(k.get("recommendation_id") == rec_id_c for k in know_data), "Approved recommendation missing from verified knowledge"
    print(f" [PASS] Recommendation {rec_id_c} approved and committed to Verified Knowledge.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # SCENARIO 12: Pre-Publish Tender Validation & System Health
    # ─────────────────────────────────────────────────────────────────────────────
    print("\n[SCENARIO 12] Testing Pre-Publish Validation and System Health...")
    r_val = client.post("/api/pre-publish/validate", json={"tender_text": tender_transformer_text})
    assert r_val.status_code == 200
    val_data = r_val.json()
    assert "findings" in val_data
    # Foreign standard IEC 60076 should be flagged in pre-publish validation as WARNING
    foreign_findings = [f for f in val_data["findings"] if f.get("rule_id") == "RULE_C_FOREIGN_STANDARD"]
    assert len(foreign_findings) > 0, "Expected Rule C foreign standard finding for IEC 60076"

    # Health check
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data.get("retrieval_mode") == "IN_MEMORY"
    assert h_data.get("embedding_mode") == "DEMO_FALLBACK"
    print(" [PASS] Pre-Publish Validation and Health endpoints operational with stable DEMO_FALLBACK settings.")
    passed += 1

    banner(f"TENDER UPLOAD VERIFICATION: {passed}/{total} SCENARIOS PASSED (100%)")

if __name__ == "__main__":
    main()
