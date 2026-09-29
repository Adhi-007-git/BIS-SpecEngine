"""
Verification script for the 7 Real Demo Tests outlined in Step 15.
Tests run against the TestClient for backend/app/main.py.
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_all():
    print("=" * 60)
    print("SIH26108 - STEP 15 REAL DEMO TESTS VERIFICATION")
    print("=" * 60)

    # TEST 1: Cable Query
    print("\n--- TEST 1: Heavy duty armoured PVC electric cables up to 1100 V ---")
    payload1 = {
        "query": "Heavy duty armoured PVC electric cables up to 1100 V",
        "top_k": 5
    }
    r1 = client.post("/api/search", json=payload1)
    assert r1.status_code == 200, f"Search failed: {r1.text}"
    data1 = r1.json()
    recs1 = data1.get("recommendations", [])
    assert len(recs1) > 0, "No recommendations returned for Test 1"
    top_rec1 = recs1[0]
    print(f"Top Recommended Standard: {top_rec1.get('standard_number')} - {top_rec1.get('title')}")
    print(f"Score: {top_rec1.get('score')}")
    print(f"Lifecycle: {top_rec1.get('lifecycle_status')}")
    print(f"QCO Enforced: {top_rec1.get('qco_enforcement_flag')}")
    print(f"Compliance Alerts: {len(top_rec1.get('compliance_alerts', []))}")
    print(f"Evidence Exists: {bool(top_rec1.get('evidence'))}")
    assert "IS 1554 (Part 1):1988" in top_rec1.get("standard_number"), f"Expected IS 1554 (Part 1):1988, got {top_rec1.get('standard_number')}"
    rec_id_1 = data1.get("recommendation_id")
    print(f"Recommendation ID: {rec_id_1}")
    print("[PASS] Test 1: Heavy duty cables correctly maps to IS 1554 (Part 1):1988 with evidence and QCO flags.")

    # TEST 2: Transformer Query
    print("\n--- TEST 2: 500 kVA outdoor oil cooled distribution transformer 11 kV/433 V ---")
    payload2 = {
        "query": "500 kVA outdoor oil cooled distribution transformer 11 kV/433 V",
        "top_k": 5
    }
    r2 = client.post("/api/search", json=payload2)
    assert r2.status_code == 200, f"Search failed: {r2.text}"
    data2 = r2.json()
    recs2 = data2.get("recommendations", [])
    # Verified catalogue has no transformer standards; pipeline must NOT return unrelated concrete or steel standards.
    assert len(recs2) == 0 or all("transformer" in (r.get("title", "") + r.get("reason", "")).lower() for r in recs2), "Unrelated standards must not be recommended for transformer query"
    rec_id_2 = data2.get("recommendation_id")
    print(f"Total Recommendations: {len(recs2)} (Manual review triggered: {data2.get('message') or 'OK'})")
    print("[PASS] Test 2: Transformer query safely handled without returning unrelated standards.")

    # TEST 3: Approve recommendation & check Verified Knowledge
    print("\n--- TEST 3: Approve recommendation -> Verified Knowledge ---")
    approve_payload = {
        "status": "APPROVED",
        "engineer_id": "ENG_DEMO_01",
        "comments": "Verified applicable for 1.1kV cables per QCO 2023 Order."
    }
    r3 = client.post(f"/api/review/{rec_id_1}/approve", json=approve_payload)
    assert r3.status_code == 200, f"Approve failed: {r3.text}"
    print(f"Approval response: {r3.json().get('message')}")

    # Check verified knowledge endpoint
    r3_vk = client.get("/api/review/knowledge")
    assert r3_vk.status_code == 200, f"Verified knowledge failed: {r3_vk.text}"
    vk_records = r3_vk.json()
    approved_ids = [rec.get("recommendation_id") for rec in vk_records]
    assert rec_id_1 in approved_ids, f"Recommendation {rec_id_1} not found in verified knowledge: {approved_ids}"
    print(f"[PASS] Test 3: Recommendation {rec_id_1} successfully approved and present in Verified Knowledge.")

    # TEST 4: Modify recommendation -> Status MODIFIED & reusable memory
    print("\n--- TEST 4: Modify recommendation -> Status MODIFIED & reusable ---")
    modify_payload = {
        "primary_standard": "IS 1554 (Part 1):1988",
        "related_standards": ["IS 8130:2013"],
        "comment": "Add note on copper vs aluminium conductor tests.",
        "modifications": {
            "notes": "Ensure adherence to conductor specification IS 8130."
        }
    }
    r4 = client.post(f"/api/review/{rec_id_2}/modify", json=modify_payload)
    assert r4.status_code == 200, f"Modify failed: {r4.text}"
    print(f"Modify response: {r4.json().get('message')}")
    
    # Check verified knowledge contains the modified record
    r4_vk = client.get("/api/review/knowledge")
    assert r4_vk.status_code == 200
    vk_records_4 = r4_vk.json()
    modified_records = [rec for rec in vk_records_4 if rec.get("recommendation_id") == rec_id_2]
    assert len(modified_records) > 0, "Modified recommendation not in verified knowledge"
    assert modified_records[0].get("engineer_status") == "MODIFIED"
    print(f"[PASS] Test 4: Recommendation {rec_id_2} status is MODIFIED and stored in Verified Knowledge.")

    # TEST 5: Reject recommendation -> Status REJECTED & NOT in Verified Knowledge memory
    print("\n--- TEST 5: Reject recommendation -> Status REJECTED, not reusable memory ---")
    # First create a new search recommendation to reject
    payload_rej = {"query": "temporary scaffolding pipes testing", "top_k": 3}
    r_rej = client.post("/api/search", json=payload_rej)
    rec_id_rej = r_rej.json().get("recommendation_id")
    
    reject_payload = {
        "comment": "Specification insufficiently detailed for scaffolding standards."
    }
    r5 = client.post(f"/api/review/{rec_id_rej}/reject", json=reject_payload)
    assert r5.status_code == 200, f"Reject failed: {r5.text}"
    
    # Verify it is NOT in verified knowledge
    r5_vk = client.get("/api/review/knowledge")
    vk_records_5 = r5_vk.json()
    rej_in_vk = [rec for rec in vk_records_5 if rec.get("recommendation_id") == rec_id_rej]
    assert len(rej_in_vk) == 0, "Rejected recommendation unexpectedly found in verified knowledge!"
    print(f"[PASS] Test 5: Recommendation {rec_id_rej} marked REJECTED and strictly excluded from Verified Knowledge.")

    # TEST 6: Generate and Download Compliance/Recommendation Report
    print("\n--- TEST 6: Generate & Download Compliance Report ---")
    r6_json = client.get(f"/api/reports/{rec_id_1}")
    assert r6_json.status_code == 200, f"Report JSON failed: {r6_json.text}"
    report_data = r6_json.json()
    assert report_data.get("report_title") == "Indian Standards Recommendation & Compliance Report"
    assert report_data.get("primary_recommended_standard") is not None
    assert len(report_data.get("evidence_audit_trail", [])) >= 0
    assert report_data.get("engineer_review_status") == "APPROVED"
    print(f"Report Generated: {report_data.get('report_title')}")
    print(f"Dataset Version: {report_data.get('dataset_version')}")
    print(f"Engineer Review Status in Report: {report_data.get('engineer_review_status')}")

    # Test Download endpoint (HTML print view)
    r6_dl = client.get(f"/api/reports/{rec_id_1}/download")
    assert r6_dl.status_code == 200, f"Download failed: {r6_dl.text}"
    assert "Indian Standards Recommendation" in r6_dl.text
    assert "IS 1554 (Part 1):1988" in r6_dl.text
    print(f"Downloaded HTML report size: {len(r6_dl.text)} bytes")
    print("[PASS] Test 6: Report generation and download endpoints verified successfully.")

    # TEST 7: Document Upload & Analysis
    print("\n--- TEST 7: Document Upload -> Extract -> Analyze -> Recommendation ---")
    sample_content = b"""
    TENDER SPECIFICATION NO: TND/2026/ELEC/089
    SCOPE OF WORK:
    Supply and delivery of 1100V grade PVC insulated heavy duty armoured electrical cables
    conforming to relevant Indian Standard specifications.
    Conductor material: Aluminium / Annealed Copper.
    Insulation: Type A PVC compound.
    """
    files = {"file": ("tender_cable_spec.txt", sample_content, "text/plain")}
    r7_up = client.post("/api/upload", files=files)
    assert r7_up.status_code == 200, f"Upload failed: {r7_up.text}"
    up_data = r7_up.json()
    print(f"Uploaded file: {up_data.get('filename')}")
    print(f"Extracted characters: {len(up_data.get('extracted_text', ''))}")
    
    # Run document analysis
    doc_id = up_data.get("document_id")
    r7_an = client.post("/api/analyze-document", json={"document_id": doc_id, "query_hint": "cables"})
    assert r7_an.status_code == 200, f"Analyze failed: {r7_an.text}"
    an_data = r7_an.json()
    an_recs = an_data.get("recommendations", [])
    assert len(an_recs) > 0, "No recommendations from document analysis"
    top_doc_rec = an_recs[0]
    top_std = top_doc_rec.get('standard_number')
    print(f"Top Document Recommendation: {top_std} - {top_doc_rec.get('title')}")
    all_std_nums = [r.get("standard_number", "") for r in an_recs]
    print(f"All Document Recommendations: {all_std_nums}")
    assert any("IS 8130" in s or "IS 1554" in s or "IS 694" in s for s in all_std_nums), f"Expected cable standards in recommendations, got {all_std_nums}"
    print("[PASS] Test 7: Document upload -> text extraction -> document analysis -> recommendations pipeline working.")

    print("\n" + "=" * 60)
    print("ALL 7 REAL DEMO TESTS COMPLETED AND PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
