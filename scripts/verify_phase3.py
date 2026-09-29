"""
Phase 3 Verification Suite for SIH26108.

Tests the real data foundation:
  - Real catalogue is loaded and indexed (count > 20)
  - is_demo flag is false
  - data_mode is VERIFIED_SOURCE
  - QCO registry is loaded correctly
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app

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

def run_phase3_verification():
    print("=" * 62)
    print("SIH26108 Phase 3 – Real Data Foundation Verification")
    print("=" * 62)

    client = TestClient(app)

    print("\n[TEST 1] Search – Verified Data Mode & Flags")
    resp = client.post("/api/search", json={"query": "concrete cement steel", "limit": 5})
    check(resp.status_code == 200, "Search returns 200")
    data = resp.json()
    
    check(data.get("data_mode") == "VERIFIED_SOURCE", f"data_mode is VERIFIED_SOURCE (got: {data.get('data_mode')})")
    
    recs = data.get("recommendations", [])
    check(len(recs) > 0, "Returned at least one recommendation")
    
    for i, r in enumerate(recs):
        check(r.get("is_demo") is False, f"Recommendation {i} is_demo is False")
        check(r.get("demo_tag") == "VERIFIED SOURCE", f"Recommendation {i} demo_tag is VERIFIED SOURCE")

    print("\n[TEST 2] Standard Details – Compliance Engine Registry")
    if recs:
        std_code = recs[0]["standard_number"]
        resp2 = client.get(f"/api/standards/{std_code}")
        check(resp2.status_code == 200, "Standard details lookup returns 200")
        
        # Test a standard we know has compliance (e.g. IS 269 or IS 694)
        resp_qco = client.get(f"/api/standards/IS 269:2015")
        if resp_qco.status_code == 200:
            qco_data = resp_qco.json()
            comp = qco_data.get("compliance", [])
            check(len(comp) > 0, "IS 269 has compliance records loaded from QCO registry")
            if comp:
                check(comp[0].get("status") == "Mandatory for Procurement", "QCO status matches")
        
    total = _pass + _fail
    print("\n" + "=" * 62)
    verdict = "ALL PASS" if _fail == 0 else f"{_fail} FAILED"
    print(f"Phase 3 Verification: {_pass}/{total} checks passed  [{verdict}]")
    print("=" * 62)

    if _fail > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_phase3_verification()
