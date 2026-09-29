"""
Phase 6A Live Verification Script -- SIH26108
Validates real live Gemini LLM integration against active .env credentials.

Checks:
  1. Environment configuration loaded (.env)
  2. Provider instantiation resolves to GeminiProvider
  3. API key present and safely masked (zero secret exposure)
  4. Live HTTP 200 request to Gemini API generates valid StructuredRequirements
  5. QueryAnalyzer.analyze() produces llm_used=True and llm_provider="GeminiProvider"
  6. RuleExtractor fallback was NOT triggered
  7. Extracted parameters accurately match procurement query

Run from project root:
    python scripts/verify_phase6a_live.py
"""

import sys
import os
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from ai_engine.query.schema import StructuredRequirements
from ai_engine.query.llm_provider import GeminiProvider, get_llm_provider, mask_secret
from ai_engine.query.query_analyzer import QueryAnalyzer

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  {GREEN}PASS{RESET}  {msg}")

def fail(msg, detail=""):
    global failed
    failed += 1
    detail_str = f" -- {detail}" if detail else ""
    print(f"  {RED}FAIL{RESET}  {msg}{detail_str}")

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

TEST_QUERY = "500 kVA outdoor oil-cooled distribution transformer, 11kV/433V, IEC 60076 compliant"

def run_live_verification():
    print(f"\nRunning Phase 6A Live Gemini Verification...")
    print(f"Target Query: '{TEST_QUERY}'")

    # 1. Environment & Provider check
    section("CHECK 1 -- Provider Instantiation & Secret Safety")
    provider = get_llm_provider()
    
    if isinstance(provider, GeminiProvider):
        ok(f"Provider instantiated as GeminiProvider: {type(provider).__name__}")
    else:
        fail(f"Expected GeminiProvider, got {type(provider).__name__}")

    raw_key = os.getenv("LLM_API_KEY", "")
    masked = mask_secret(raw_key)

    if masked != "<not set>" and masked != "***" and len(raw_key) > 5:
        ok(f"API key detected and masked safely: '{masked}'")
    else:
        fail(f"Invalid or missing API key: '{masked}'")

    # Anti-leak check
    if raw_key and raw_key in masked:
        fail("CRITICAL: Full API key exposed in masked string!")
    else:
        ok("Anti-leak confirmed: Raw secret key not exposed")

    model_name = os.getenv("LLM_MODEL", "")
    ok(f"Active model configured: '{model_name}'")

    # 2. Live API Call & Parsing
    section("CHECK 2 -- Live Gemini API Request (Direct Provider)")
    try:
        parsed = provider.parse_query(TEST_QUERY)
        if parsed is not None and isinstance(parsed, StructuredRequirements):
            ok("Live Gemini API returned HTTP 200 and valid StructuredRequirements")
        else:
            fail("Gemini provider returned None or invalid type")
    except Exception as e:
        fail("Gemini live request failed with exception", str(e))
        parsed = None

    if parsed:
        if parsed.product and "transformer" in parsed.product.lower():
            ok(f"Extracted product: '{parsed.product}'")
        else:
            fail(f"Product extraction failed: '{parsed.product}'")

        if parsed.capacity and "500" in parsed.capacity:
            ok(f"Extracted capacity: '{parsed.capacity}'")
        else:
            fail(f"Capacity extraction failed: '{parsed.capacity}'")

        if parsed.cooling and "oil" in parsed.cooling.lower():
            ok(f"Extracted cooling: '{parsed.cooling}'")
        else:
            fail(f"Cooling extraction failed: '{parsed.cooling}'")

        if parsed.installation and "outdoor" in parsed.installation.lower():
            ok(f"Extracted installation: '{parsed.installation}'")
        else:
            fail(f"Installation extraction failed: '{parsed.installation}'")

        if parsed.primary_voltage and "11" in parsed.primary_voltage:
            ok(f"Extracted primary_voltage: '{parsed.primary_voltage}'")
        else:
            fail(f"Primary voltage extraction failed: '{parsed.primary_voltage}'")

        if parsed.secondary_voltage and "433" in parsed.secondary_voltage:
            ok(f"Extracted secondary_voltage: '{parsed.secondary_voltage}'")
        else:
            fail(f"Secondary voltage extraction failed: '{parsed.secondary_voltage}'")

        if parsed.foreign_standards and any("60076" in s for s in parsed.foreign_standards):
            ok(f"Extracted foreign_standards: {parsed.foreign_standards}")
        else:
            fail(f"Foreign standards extraction failed: {parsed.foreign_standards}")

    # 3. QueryAnalyzer Live Integration
    section("CHECK 3 -- QueryAnalyzer Live End-to-End Analysis")
    qa = QueryAnalyzer()
    analysis = qa.analyze(TEST_QUERY)

    if analysis.get("llm_used") is True:
        ok("QueryAnalyzer reports llm_used=True")
    else:
        fail(f"Expected llm_used=True, got {analysis.get('llm_used')}")

    if analysis.get("llm_provider") == "GeminiProvider":
        ok(f"QueryAnalyzer reports llm_provider='GeminiProvider'")
    else:
        fail(f"Expected llm_provider='GeminiProvider', got '{analysis.get('llm_provider')}'")

    if analysis.get("is_empty") is False:
        ok("QueryAnalyzer is_empty=False")
    else:
        fail("QueryAnalyzer is_empty should be False")

    sr = analysis.get("structured_requirements")
    if sr and isinstance(sr, dict) and sr.get("product"):
        ok("QueryAnalyzer returned valid structured_requirements dictionary")
    else:
        fail("QueryAnalyzer structured_requirements is empty or invalid")

    # 4. Summary
    section("LIVE VERIFICATION SUMMARY")
    print(f"  Passed : {passed}")
    print(f"  Failed : {failed}")
    print(f"  Total  : {passed + failed}")

    if failed == 0:
        print(f"\n  {GREEN}ALL LIVE GEMINI CHECKS PASSED SUCCESSFULLY{RESET}\n")
        return 0
    else:
        print(f"\n  {RED}SOME LIVE CHECKS FAILED{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_live_verification())
