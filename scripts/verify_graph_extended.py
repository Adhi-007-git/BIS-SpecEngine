"""
Extended Verification Suite for M3: Knowledge Graph.
Validates:
1. Retrieval of standards catalogue for dynamic selector (GET /api/standards).
2. Graph generation for standards with SUPERSEDES relationships (e.g., IS 456:2000).
3. Graph generation for standards with REQUIRES_TESTING_VIA relationships (e.g., IS 456:2000 -> IS 516:1959).
4. Graph generation for standards with SPECIFIES_MATERIAL relationships (e.g., IS 1554 -> IS 8130).
5. Graph generation for standards with GOVERNED_BY_SAFETY relationships (e.g., IS 732 -> IS/IEC 60529).
6. Graph generation for standards with MANDATED_BY QCO relationships (e.g., IS 694 -> Electrical Wires QCO).
7. Standards with zero relationships (isolated root node, 0 edges, non-crashing).
8. Unresolved external target standard handling (does not crash).
9. Test fixture with synthetic relationships explicitly labelled as TEST_FIXTURE.
10. Backward-compatible GraphResponse schema (nodes, edges, total_nodes, total_edges).
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app
from ai_engine.knowledge_graph.graph_builder import GraphBuilder
from ai_engine.knowledge_graph.neo4j_service import Neo4jService

client = TestClient(app)

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"

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

def run_tests():
    print("=" * 65)
    print("SIH26108 - M3 KNOWLEDGE GRAPH EXTENDED VERIFICATION")
    print("=" * 65)

    # TEST 1: Catalogue listing endpoint for dynamic selector
    print("\n[TEST 1] Testing GET /api/standards (Dynamic Catalogue Selector)...")
    res = client.get("/api/standards")
    check(res.status_code == 200, "GET /api/standards returns 200 OK")
    stds = res.json()
    check(len(stds) >= 21, f"Returns at least 21 catalogue standards (got {len(stds)})")
    if stds:
        s0 = stds[0]
        check("standard_number" in s0 and "title" in s0, "Standards contain standard_number and title")
        print(f"       Sample standard: {s0['standard_number']} - {s0['title'][:40]}...")

    # TEST 2: Verified SUPERSEDES & REQUIRES_TESTING_VIA on IS 456:2000
    print("\n[TEST 2] Testing GET /api/graph/IS 456:2000 (SUPERSEDES & REQUIRES_TESTING_VIA)...")
    res_456 = client.get("/api/graph/IS 456:2000")
    check(res_456.status_code == 200, "IS 456:2000 graph endpoint returns 200 OK")
    g_456 = res_456.json()
    check(g_456["total_nodes"] >= 3, f"IS 456 has multiple connected nodes (got {g_456['total_nodes']})")
    labels_456 = [e["label"] for e in g_456["edges"]]
    check("SUPERSEDES" in labels_456, "Contains SUPERSEDES edge to IS 456:1978")
    check("REQUIRES TESTING VIA" in labels_456, "Contains REQUIRES_TESTING_VIA edge to IS 516:1959")
    check("SPECIFIES MATERIAL" in labels_456, "Contains SPECIFIES_MATERIAL edge to IS 383:2016")

    # TEST 3: Verified SPECIFIES_MATERIAL & MANDATED_BY on IS 1554 (Part 1):1988
    print("\n[TEST 3] Testing GET /api/graph/IS 1554 (Part 1):1988 (SPECIFIES_MATERIAL & QCO)...")
    res_1554 = client.get("/api/graph/IS 1554 (Part 1):1988")
    check(res_1554.status_code == 200, "IS 1554 graph returns 200 OK")
    g_1554 = res_1554.json()
    labels_1554 = [e["label"] for e in g_1554["edges"]]
    check("SPECIFIES MATERIAL" in labels_1554, "Contains SPECIFIES_MATERIAL edge (conductors IS 8130)")
    check("MANDATED BY" in labels_1554, "Contains MANDATED_BY edge (Cables QCO)")

    # TEST 4: Verified GOVERNED_BY_SAFETY on IS 732:2019
    print("\n[TEST 4] Testing GET /api/graph/IS 732:2019 (GOVERNED_BY_SAFETY)...")
    res_732 = client.get("/api/graph/IS 732:2019")
    check(res_732.status_code == 200, "IS 732 graph returns 200 OK")
    g_732 = res_732.json()
    labels_732 = [e["label"] for e in g_732["edges"]]
    check("GOVERNED BY SAFETY" in labels_732, "Contains GOVERNED_BY_SAFETY edge (IS/IEC 60529 IP Code)")

    # TEST 5: Isolated standard with no linked relationships (Empty edge state)
    print("\n[TEST 5] Testing standard with no linked relationships (IS 516:1959)...")
    res_516 = client.get("/api/graph/IS 516:1959")
    check(res_516.status_code == 200, "Isolated standard returns 200 OK without crashing")
    g_516 = res_516.json()
    check(g_516["total_nodes"] == 1, f"Isolated standard retains exactly 1 root node (got {g_516['total_nodes']})")
    check(g_516["total_edges"] == 0, f"Isolated standard has 0 edges (got {g_516['total_edges']})")

    # TEST 6: Unresolved target standard handling
    print("\n[TEST 6] Testing unresolved target standard lookup...")
    res_missing = client.get("/api/graph/NON_EXISTENT_STANDARD_999")
    check(res_missing.status_code == 404, "Non-existent standard safely returns 404 without server crash")

    # TEST 7: Synthetic GraphBuilder Fixture (Clearly labelled as TEST_FIXTURE)
    print("\n[TEST 7] Testing GraphBuilder with synthetic TEST_FIXTURE data...")
    builder = GraphBuilder()
    synthetic_primary = {
        "standard_number": "IS 99999:2026",
        "title": "TEST_FIXTURE: Synthetic Spec for Graph Verification",
        "status": "Active"
    }
    synthetic_related = [
        {"standard_number": "IS 99991:2020", "title": "TEST_FIXTURE: Testing Reference", "relation": "REQUIRES_TESTING_VIA"},
        {"standard_number": "IS 99992:2021", "title": "TEST_FIXTURE: Material Specification", "relation": "SPECIFIES_MATERIAL"},
        {"standard_number": "IS 99993:2022", "title": "TEST_FIXTURE: Safety Guideline", "relation": "GOVERNED_BY_SAFETY"},
        {"standard_number": "IS 99994:2023", "title": "TEST_FIXTURE: Normative Reference", "relation": "NORMATIVE_REFERENCE"},
        {"standard_number": "QCO ORDER 2026", "title": "TEST_FIXTURE: Mandatory Order", "relation": "MANDATED_BY"}
    ]
    graph_res = builder.build_flow_graph(synthetic_primary, synthetic_related)
    check(graph_res["total_nodes"] == 6, f"Root + 5 related nodes created (got {graph_res['total_nodes']})")
    check(graph_res["total_edges"] == 5, f"5 edges created (got {graph_res['total_edges']})")
    
    # Verify edge directions: MANDATED_BY must point TO root, others FROM root
    edges = graph_res["edges"]
    qco_edge = next((e for e in edges if e["label"] == "MANDATED BY"), None)
    check(qco_edge is not None and qco_edge["target"] == "root", "MANDATED_BY edge targets root node")
    test_edge = next((e for e in edges if e["label"] == "REQUIRES TESTING VIA"), None)
    check(test_edge is not None and test_edge["source"] == "root" and test_edge.get("animated") is True, "REQUIRES_TESTING_VIA edge is animated from root")

    total = _pass + _fail
    print("\n" + "=" * 65)
    verdict = "ALL PASS" if _fail == 0 else f"{_fail} FAILED"
    print(f"M3 Extended Graph Verification: {_pass}/{total} checks passed  [{verdict}]")
    print("=" * 65)

    if _fail > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
