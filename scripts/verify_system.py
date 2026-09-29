"""
End-to-End System Verification for SIH26108.
Tests health check, natural-language semantic query, evidence verification,
compliance mandates, and knowledge graph generation.
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on python path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app

def run_verification():
    print("==================================================")
    print("SIH26108 - End-to-End Automated Verification Test")
    print("==================================================")
    client = TestClient(app)

    # Test 1: Health Check
    print("\n[TEST 1] Verifying /api/health...")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f" [PASS] Status: {health_data['status']}, Environment: {health_data['environment']}, Dev Mode: {health_data['dev_mode']}")

    # Test 2: Natural Language Query Pipeline
    query = "building materials concrete steel"
    print(f"\n[TEST 2] Testing /api/search with query:\n  '{query}'...")
    search_resp = client.post("/api/search", json={"query": query, "limit": 5})
    assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
    search_data = search_resp.json()
    
    rec_id = search_data["recommendation_id"]
    recommendations = search_data["recommendations"]
    print(f" [PASS] Generated Recommendation ID: {rec_id}")
    print(f" [PASS] Total Recommendations: {len(recommendations)} (Data Mode: {search_data['data_mode']})")
    
    assert len(recommendations) > 0, "No recommendations returned!"
    first_rec = recommendations[0]
    print(f" Top Standard: {first_rec['standard_number']} ({first_rec['title'][:50]}...)")
    print(f" Relevance: {round(first_rec['relevance_score'] * 100)}%")
    print(f" Reason: {first_rec['reason']}")
    print(f" Evidence: Page {first_rec.get('page')}, Section {first_rec.get('section')}: '{first_rec.get('evidence')[:70]}...'")
    print(f" Compliance: {len(first_rec.get('compliance', []))} items")
    print(f" Demo Tag: {first_rec.get('demo_tag')}")

    # Test 3: Standard Details Lookup
    std_code = first_rec['standard_number']
    print(f"\n[TEST 3] Testing /api/standards/{std_code}...")
    std_resp = client.get(f"/api/standards/{std_code}")
    assert std_resp.status_code == 200, f"Standard lookup failed: {std_resp.text}"
    std_data = std_resp.json()
    print(f" [PASS] Title: {std_data['title'][:60]}...")
    print(f" [PASS] Normative References: {len(std_data['normative_references'])}")
    print(f" [PASS] Test Methods: {len(std_data['test_methods'])}")

    # Test 4: Evidence Audit Trail
    print(f"\n[TEST 4] Testing /api/evidence/{rec_id}...")
    ev_resp = client.get(f"/api/evidence/{rec_id}")
    assert ev_resp.status_code == 200, f"Evidence lookup failed: {ev_resp.text}"
    ev_data = ev_resp.json()
    print(f" [PASS] Retrieved {len(ev_data)} evidence audit records for session {rec_id}.")

    # Test 5: Knowledge Graph Generation for React Flow
    print(f"\n[TEST 5] Testing /api/graph/{std_code} for React Flow...")
    graph_resp = client.get(f"/api/graph/{std_code}")
    assert graph_resp.status_code == 200, f"Graph lookup failed: {graph_resp.text}"
    graph_data = graph_resp.json()
    print(f" [PASS] Total Graph Nodes: {graph_data['total_nodes']}, Total Edges: {graph_data['total_edges']}")
    for edge in graph_data['edges'][:3]:
        print(f"   - Edge: {edge['source']} --[{edge.get('label')}]--> {edge['target']}")

    print("\n==================================================")
    print("ALL 5 SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
