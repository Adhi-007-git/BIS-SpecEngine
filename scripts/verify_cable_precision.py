"""
SIH26108 Cable Recommendation Precision & Hard Compatibility Regression Suite
=============================================================================
Tests all 6 required precision and compliance scenarios:
1. 1100 V PVC cable (English + Hindi): Only IS 1554 (Part 1):1988 directly applicable;
   IS 694 (voltage conflict) and IS 7098 (insulation conflict) excluded.
2. 450/750 V PVC cable: IS 694:2010 directly applicable; IS 7098 Pt 1 excluded.
3. 1100 V XLPE cable: IS 7098 (Part 1):1988 directly applicable; IS 1554 Pt 1 excluded.
4. Conflicting or out-of-scope voltage (33 kV PVC cable): 0 direct recs, voltage conflict message.
5. Missing technical parameters (missing voltage, missing insulation):
   Flagged with officer_verification_needed = True and advisory notices.
6. QCO applicability without verified matching record:
   Only verified mandatory QCO standards get qco_enforcement_flag = True.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app
from ai_engine.query.query_analyzer import QueryAnalyzer
from ai_engine.reranker.reranker import Reranker
from ai_engine.recommendation.recommendation_generator import RecommendationGenerator

client = TestClient(app)

passed = 0
failed = 0

def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} -- {detail}")


print("=" * 75)
print("SIH26108: CABLE RECOMMENDATION PRECISION & COMPATIBILITY REGRESSION SUITE")
print("=" * 75)

# ─── TEST 1: 1100 V PVC HEAVY DUTY CABLE (ENGLISH & HINDI) ────────────────────
print("\n[TEST 1] 1100 V PVC Heavy Duty Cable (English & Hindi)")

# 1A: English Query
res_en = client.post("/api/search", json={"query": "1100 V PVC heavy duty electric cable"})
check("1A.1 English Search Status 200", res_en.status_code == 200)
data_en = res_en.json()
recs_en = data_en.get("recommendations", [])
rec_std_nums_en = [r["standard_number"] for r in recs_en]
print(f"   English Direct Recommendations: {rec_std_nums_en}")

check(
    "1A.2 IS 1554 (Part 1):1988 is directly applicable",
    "IS 1554 (Part 1):1988" in rec_std_nums_en,
    f"Found: {rec_std_nums_en}"
)
if "IS 1554 (Part 1):1988" in rec_std_nums_en:
    r1554 = next(r for r in recs_en if r["standard_number"] == "IS 1554 (Part 1):1988")
    check("1A.3 IS 1554 marked DIRECTLY_APPLICABLE", r1554.get("applicability_type") == "DIRECTLY_APPLICABLE")

check(
    "1A.4 IS 694:2010 excluded as direct match (voltage conflict: 1100 V > 750 V)",
    "IS 694:2010" not in rec_std_nums_en,
    f"IS 694 found in: {rec_std_nums_en}"
)
check(
    "1A.5 IS 7098 (Part 1):1988 excluded as direct match (insulation conflict: XLPE != PVC)",
    "IS 7098 (Part 1):1988" not in rec_std_nums_en,
    f"IS 7098 found in: {rec_std_nums_en}"
)

# Check excluded candidates audit trail
excl_en = data_en.get("excluded_candidates", [])
excl_map_en = {e["standard_number"]: e["exclusion_reason"] for e in excl_en}
check(
    "1A.6 Excluded candidates audit log contains IS 694:2010 with voltage reason",
    "IS 694:2010" in excl_map_en and "voltage" in excl_map_en["IS 694:2010"].lower(),
    f"Audit log: {excl_map_en.get('IS 694:2010')}"
)
check(
    "1A.7 Excluded candidates audit log contains IS 7098 (Part 1):1988 with insulation reason",
    "IS 7098 (Part 1):1988" in excl_map_en and ("insulation" in excl_map_en["IS 7098 (Part 1):1988"].lower() or "xlpe" in excl_map_en["IS 7098 (Part 1):1988"].lower()),
    f"Audit log: {excl_map_en.get('IS 7098 (Part 1):1988')}"
)

# 1B: Hindi Query (Reproducing user case: 1100 V पीवीसी भारी विद्युत केबल)
res_hi = client.post("/api/search", json={"query": "1100 V पीवीसी भारी विद्युत केबल"})
check("1B.1 Hindi Search Status 200", res_hi.status_code == 200)
data_hi = res_hi.json()
recs_hi = data_hi.get("recommendations", [])
rec_std_nums_hi = [r["standard_number"] for r in recs_hi]
print(f"   Hindi Direct Recommendations: {rec_std_nums_hi}")

check(
    "1B.2 Hindi query retains IS 1554 (Part 1):1988",
    "IS 1554 (Part 1):1988" in rec_std_nums_hi,
    f"Found: {rec_std_nums_hi}"
)
check(
    "1B.3 Hindi query excludes IS 694:2010",
    "IS 694:2010" not in rec_std_nums_hi,
    f"Found: {rec_std_nums_hi}"
)
check(
    "1B.4 Hindi query excludes IS 7098 (Part 1):1988",
    "IS 7098 (Part 1):1988" not in rec_std_nums_hi,
    f"Found: {rec_std_nums_hi}"
)


# ─── TEST 2: 450/750 V PVC CABLE ──────────────────────────────────────────────
print("\n[TEST 2] 450/750 V PVC Cable")
res_450 = client.post("/api/search", json={"query": "450/750 V PVC cable"})
check("2.1 Search Status 200", res_450.status_code == 200)
data_450 = res_450.json()
recs_450 = data_450.get("recommendations", [])
rec_std_nums_450 = [r["standard_number"] for r in recs_450]
print(f"   450/750 V Direct Recommendations: {rec_std_nums_450}")

check(
    "2.2 IS 694:2010 is directly applicable for 450/750 V PVC",
    "IS 694:2010" in rec_std_nums_450,
    f"Found: {rec_std_nums_450}"
)
if "IS 694:2010" in rec_std_nums_450:
    r694 = next(r for r in recs_450 if r["standard_number"] == "IS 694:2010")
    check("2.3 IS 694 marked DIRECTLY_APPLICABLE", r694.get("applicability_type") == "DIRECTLY_APPLICABLE")

check(
    "2.4 IS 7098 (Part 1):1988 excluded (material conflict XLPE vs PVC)",
    "IS 7098 (Part 1):1988" not in rec_std_nums_450,
    f"Found: {rec_std_nums_450}"
)


# ─── TEST 3: 1100 V XLPE CABLE ────────────────────────────────────────────────
print("\n[TEST 3] 1100 V XLPE Cable")
res_xlpe = client.post("/api/search", json={"query": "1100 V XLPE insulated heavy duty cable"})
check("3.1 Search Status 200", res_xlpe.status_code == 200)
data_xlpe = res_xlpe.json()
recs_xlpe = data_xlpe.get("recommendations", [])
rec_std_nums_xlpe = [r["standard_number"] for r in recs_xlpe]
print(f"   1100 V XLPE Direct Recommendations: {rec_std_nums_xlpe}")

check(
    "3.2 IS 7098 (Part 1):1988 is directly applicable for 1100 V XLPE",
    "IS 7098 (Part 1):1988" in rec_std_nums_xlpe,
    f"Found: {rec_std_nums_xlpe}"
)
if "IS 7098 (Part 1):1988" in rec_std_nums_xlpe:
    r7098 = next(r for r in recs_xlpe if r["standard_number"] == "IS 7098 (Part 1):1988")
    check("3.3 IS 7098 Pt 1 marked DIRECTLY_APPLICABLE", r7098.get("applicability_type") == "DIRECTLY_APPLICABLE")

check(
    "3.4 IS 1554 (Part 1):1988 excluded as direct match (material conflict: PVC vs XLPE)",
    "IS 1554 (Part 1):1988" not in rec_std_nums_xlpe,
    f"Found: {rec_std_nums_xlpe}"
)
check(
    "3.5 IS 694:2010 excluded as direct match (voltage & material conflict)",
    "IS 694:2010" not in rec_std_nums_xlpe,
    f"Found: {rec_std_nums_xlpe}"
)


# ─── TEST 4: CONFLICTING / OUT-OF-RANGE VOLTAGE (33 kV PVC CABLE) ─────────────
print("\n[TEST 4] Conflicting / Out-of-Range Voltage (33 kV PVC Cable)")
res_33kv = client.post("/api/search", json={"query": "33 kV PVC heavy duty power cable"})
check("4.1 Search Status 200", res_33kv.status_code == 200)
data_33kv = res_33kv.json()
recs_33kv = data_33kv.get("recommendations", [])
print(f"   33 kV Direct Recommendations count: {len(recs_33kv)}")

check(
    "4.2 No low/medium voltage standards falsely recommended for 33 kV",
    len(recs_33kv) == 0,
    f"Found: {[r['standard_number'] for r in recs_33kv]}"
)
msg = data_33kv.get("message", "")
check(
    "4.3 Voltage conflict or officer review message provided",
    "voltage" in msg.lower() or "officer" in msg.lower() or "withheld" in msg.lower(),
    f"Message: {msg}"
)


# ─── TEST 5: MISSING OR UNCERTAIN TECHNICAL PARAMETERS ─────────────────────────
print("\n[TEST 5] Missing Technical Parameters (Missing Voltage / Missing Insulation)")

# 5A: Missing Voltage
res_miss_v = client.post("/api/search", json={"query": "PVC insulated electric power cable"})
check("5A.1 Search Status 200", res_miss_v.status_code == 200)
data_miss_v = res_miss_v.json()
adv_v = data_miss_v.get("advisory_notices", [])
recs_miss_v = data_miss_v.get("recommendations", [])
print(f"   Missing Voltage Advisories: {adv_v}")

check(
    "5A.2 Advisory notice issued for missing rated voltage",
    any("voltage" in a.lower() for a in adv_v),
    f"Advisories: {adv_v}"
)
check(
    "5A.3 Recommendations flag officer_verification_needed = True",
    any(r.get("officer_verification_needed") is True for r in recs_miss_v),
    f"Items: {[(r['standard_number'], r.get('officer_verification_needed')) for r in recs_miss_v]}"
)

# 5B: Missing Insulation
res_miss_mat = client.post("/api/search", json={"query": "1100 V electric cable for industrial feeder"})
check("5B.1 Search Status 200", res_miss_mat.status_code == 200)
data_miss_mat = res_miss_mat.json()
adv_mat = data_miss_mat.get("advisory_notices", [])
recs_miss_mat = data_miss_mat.get("recommendations", [])
print(f"   Missing Insulation Advisories: {adv_mat}")

check(
    "5B.2 Advisory notice issued for missing insulation material",
    any("insulation" in a.lower() for a in adv_mat),
    f"Advisories: {adv_mat}"
)
check(
    "5B.3 Recommendations flag officer_verification_needed = True",
    any(r.get("officer_verification_needed") is True for r in recs_miss_mat),
    f"Items: {[(r['standard_number'], r.get('officer_verification_needed')) for r in recs_miss_mat]}"
)


# ─── TEST 6: QCO APPLICABILITY WITHOUT VERIFIED MATCHING RECORD ─────────────────
print("\n[TEST 6] QCO Enforcement Flag Accuracy Without Verified Matching Record")

# Search for mild steel tubes (IS 1239 Pt 1) which is not in the mandatory QCO registry
res_steel = client.post("/api/search", json={"query": "mild steel tubes for water and gas"})
check("6.1 Steel Search Status 200", res_steel.status_code == 200)
data_steel = res_steel.json()
recs_steel = data_steel.get("recommendations", [])
std_1239 = next((r for r in recs_steel if "IS 1239" in r["standard_number"]), None)

if std_1239:
    check(
        "6.2 IS 1239 (Part 1):2004 does NOT have false QCO mandatory enforcement flag",
        std_1239.get("qco_enforcement_flag") is False,
        f"qco_enforcement_flag is: {std_1239.get('qco_enforcement_flag')}"
    )
    compliance = std_1239.get("compliance_alerts", [])
    check(
        "6.3 IS 1239 compliance alert does NOT falsely claim mandatory procurement order",
        not any("mandatory for procurement" in str(alert).lower() for alert in compliance),
        f"Alerts: {compliance}"
    )
else:
    print("   [SKIP] IS 1239 not in top recommendations for mild steel tubes")

# Search for ordinary portland cement (IS 269:2015) which IS in the mandatory QCO registry
res_cement = client.post("/api/search", json={"query": "ordinary portland cement 43 grade for general construction"})
check("6.4 Cement Search Status 200", res_cement.status_code == 200)
data_cement = res_cement.json()
recs_cement = data_cement.get("recommendations", [])
std_269 = next((r for r in recs_cement if "IS 269" in r["standard_number"]), None)

if std_269:
    check(
        "6.5 IS 269:2015 correctly retains verified mandatory QCO enforcement flag",
        std_269.get("qco_enforcement_flag") is True,
        f"qco_enforcement_flag is: {std_269.get('qco_enforcement_flag')}"
    )

# Also verify that IS 1554 (Part 1) from Test 1 retains verified mandatory QCO flag
if "IS 1554 (Part 1):1988" in rec_std_nums_en:
    r1554 = next(r for r in recs_en if r["standard_number"] == "IS 1554 (Part 1):1988")
    check(
        "6.6 IS 1554 (Part 1):1988 correctly has verified mandatory QCO flag",
        r1554.get("qco_enforcement_flag") is True,
        f"qco_enforcement_flag is: {r1554.get('qco_enforcement_flag')}"
    )


print("\n" + "=" * 75)
print(f"REGRESSION SUITE COMPLETED: {passed} PASSED, {failed} FAILED")
print("=" * 75)

if failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
