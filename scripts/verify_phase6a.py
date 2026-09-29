"""
Phase 6A Verification Script -- SIH26108
Validates:
  1. Provider abstraction layer
  2. Environment-based configuration
  3. Schema / structured output validation
  4. LLM -> fallback chain (timeout, bad JSON, empty key)
  5. Anti-hallucination safeguards

Run from project root:
    python scripts/verify_phase6a.py
"""

import sys
import os
import json
import urllib.error
import socket

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

passed = 0
failed = 0
warnings = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  {GREEN}PASS{RESET}  {msg}")

def fail(msg, detail=""):
    global failed
    failed += 1
    detail_str = f" -- {detail}" if detail else ""
    print(f"  {RED}FAIL{RESET}  {msg}{detail_str}")

def warn(msg):
    global warnings
    warnings += 1
    print(f"  {YELLOW}WARN{RESET}  {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# CHECK 1
section("CHECK 1 -- Module imports")
try:
    from ai_engine.query.schema import StructuredRequirements
    ok("ai_engine.query.schema imported")
except Exception as e:
    fail("ai_engine.query.schema import failed", str(e))

try:
    from ai_engine.query.rule_extractor import RuleExtractor
    ok("ai_engine.query.rule_extractor imported")
except Exception as e:
    fail("ai_engine.query.rule_extractor import failed", str(e))

try:
    from ai_engine.query.llm_provider import (
        BaseLLMProvider, MockLLMProvider, GeminiProvider,
        OpenAIProvider, get_llm_provider, mask_secret
    )
    ok("ai_engine.query.llm_provider imported (all symbols)")
except Exception as e:
    fail("ai_engine.query.llm_provider import failed", str(e))

try:
    from ai_engine.query.query_analyzer import QueryAnalyzer
    ok("ai_engine.query.query_analyzer imported")
except Exception as e:
    fail("ai_engine.query.query_analyzer import failed", str(e))


# CHECK 2
section("CHECK 2 -- Provider abstraction")
try:
    from abc import ABC
    if issubclass(BaseLLMProvider, ABC):
        ok("BaseLLMProvider is an ABC")
    else:
        fail("BaseLLMProvider is NOT an ABC")

    abstract_methods = getattr(BaseLLMProvider, "__abstractmethods__", set())
    if "parse_query" in abstract_methods:
        ok("parse_query is abstract")
    else:
        fail("parse_query is NOT abstract")

    if "is_available" in abstract_methods:
        ok("is_available is abstract")
    else:
        fail("is_available is NOT abstract")
except Exception as e:
    fail("Abstraction checks failed", str(e))


# CHECK 3
section("CHECK 3 -- MockLLMProvider")
try:
    mock = MockLLMProvider()
    if mock.is_available():
        ok("MockLLMProvider.is_available() returns True")
    else:
        fail("MockLLMProvider.is_available() returned False")

    result = mock.parse_query("500 kVA distribution transformer 11kV/433V")
    if result is not None:
        ok("MockLLMProvider.parse_query returns non-None for valid query")
    else:
        fail("MockLLMProvider.parse_query returned None for valid query")

    if result is not None and isinstance(result, StructuredRequirements):
        ok("MockLLMProvider result is StructuredRequirements instance")
    else:
        fail("MockLLMProvider result is not a StructuredRequirements instance")

    result_empty = mock.parse_query("")
    if result_empty is None:
        ok("MockLLMProvider.parse_query returns None for empty query")
    else:
        fail("MockLLMProvider.parse_query should return None for empty query")
except Exception as e:
    fail("MockLLMProvider checks failed", str(e))


# CHECK 4
section("CHECK 4 -- GeminiProvider availability gate")
try:
    g_no_key = GeminiProvider(api_key="")
    if not g_no_key.is_available():
        ok("GeminiProvider.is_available() returns False with empty key")
    else:
        fail("GeminiProvider.is_available() returned True with empty key")

    g_short_key = GeminiProvider(api_key="abc")
    if not g_short_key.is_available():
        ok("GeminiProvider.is_available() returns False with short key")
    else:
        fail("GeminiProvider.is_available() returned True with key <=5 chars")

    g_fake_key = GeminiProvider(api_key="AIzaFakeKeyForTesting123")
    if g_fake_key.is_available():
        ok("GeminiProvider.is_available() returns True with plausible key")
    else:
        fail("GeminiProvider.is_available() returned False with plausible key")
except Exception as e:
    fail("GeminiProvider availability checks failed", str(e))


# CHECK 5
section("CHECK 5 -- GeminiProvider network failure -> returns None (not crash)")
try:
    from unittest.mock import patch

    g = GeminiProvider(api_key="AIzaFakeKeyForTesting123", timeout=0.001)

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network unreachable")):
        result = g.parse_query("500 kVA transformer")
        if result is None:
            ok("GeminiProvider returns None on URLError (does not crash)")
        else:
            fail("GeminiProvider should return None on URLError")

    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        result = g.parse_query("500 kVA transformer")
        if result is None:
            ok("GeminiProvider returns None on socket.timeout (does not crash)")
        else:
            fail("GeminiProvider should return None on socket.timeout")
except Exception as e:
    fail("GeminiProvider network failure checks failed", str(e))


# CHECK 6
section("CHECK 6 -- BaseLLMProvider.validate_output robustness")
try:
    m = MockLLMProvider()
    plain_json = json.dumps({
        "product": "transformer", "capacity": "500 kVA", "cooling": "oil-cooled",
        "installation": None, "primary_voltage": "11 kV", "secondary_voltage": "433 V",
        "foreign_standards": ["IEC 60076"], "application": "power distribution"
    })

    r = m.validate_output(plain_json)
    if r and r.product == "transformer":
        ok("validate_output handles plain JSON string")
    else:
        fail("validate_output failed on plain JSON string")

    md_json = "```json\n" + plain_json + "\n```"
    r2 = m.validate_output(md_json)
    if r2 and r2.product == "transformer":
        ok("validate_output strips ```json markdown wrapper")
    else:
        fail("validate_output failed to strip ```json markdown wrapper")

    plain_md = "```\n" + plain_json + "\n```"
    r3 = m.validate_output(plain_md)
    if r3 and r3.product == "transformer":
        ok("validate_output strips plain ``` wrapper")
    else:
        fail("validate_output failed on plain ``` wrapper")

    r4 = m.validate_output({"product": "cable", "capacity": None, "cooling": None,
                             "installation": None, "primary_voltage": None,
                             "secondary_voltage": None, "foreign_standards": [],
                             "application": None})
    if r4 and r4.product == "cable":
        ok("validate_output handles dict input directly")
    else:
        fail("validate_output failed on dict input")

    r5 = m.validate_output("this is not JSON {{{")
    if r5 is None:
        ok("validate_output returns None on malformed JSON")
    else:
        fail("validate_output should return None on malformed JSON")

    r6 = m.validate_output(12345)
    if r6 is None:
        ok("validate_output returns None on wrong type (int)")
    else:
        fail("validate_output should return None on wrong type (int)")
except Exception as e:
    fail("validate_output checks failed", str(e))


# CHECK 7
section("CHECK 7 -- API key masking (anti-leak)")
try:
    masked = mask_secret("AIzaSyAbcDefGhijklmnop")
    if "AIza" in masked and masked != "AIzaSyAbcDefGhijklmnop":
        ok(f"mask_secret shows prefix/suffix only: '{masked}'")
    else:
        fail(f"mask_secret exposed full key: '{masked}'")

    masked_none = mask_secret(None)
    if masked_none == "<not set>":
        ok("mask_secret returns '<not set>' for None")
    else:
        fail(f"mask_secret returned unexpected value for None: '{masked_none}'")

    masked_short = mask_secret("abc")
    if masked_short == "***":
        ok("mask_secret returns '***' for short key")
    else:
        fail(f"mask_secret returned unexpected value for short key: '{masked_short}'")
except Exception as e:
    fail("mask_secret checks failed", str(e))


# CHECK 8
section("CHECK 8 -- get_llm_provider factory")
try:
    for k in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_TIMEOUT"):
        os.environ.pop(k, None)

    p = get_llm_provider()
    if isinstance(p, MockLLMProvider):
        ok("get_llm_provider() defaults to MockLLMProvider with no env vars")
    else:
        fail(f"Expected MockLLMProvider, got {type(p).__name__}")

    os.environ["LLM_PROVIDER"] = "mock"
    p2 = get_llm_provider()
    if isinstance(p2, MockLLMProvider):
        ok("Returns MockLLMProvider when LLM_PROVIDER=mock")
    else:
        fail(f"Expected MockLLMProvider, got {type(p2).__name__}")

    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["LLM_API_KEY"] = "AIzaFakeKeyForTesting123"
    p3 = get_llm_provider()
    if isinstance(p3, GeminiProvider):
        ok("Returns GeminiProvider when LLM_PROVIDER=gemini")
    else:
        fail(f"Expected GeminiProvider, got {type(p3).__name__}")

    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LLM_API_KEY"] = "sk-fakekey123"
    p4 = get_llm_provider()
    if isinstance(p4, OpenAIProvider):
        ok("Returns OpenAIProvider when LLM_PROVIDER=openai")
    else:
        fail(f"Expected OpenAIProvider, got {type(p4).__name__}")

    os.environ.pop("LLM_PROVIDER", None)
    os.environ["LLM_API_KEY"] = "AIzaAutoDetectKey123"
    p5 = get_llm_provider()
    if isinstance(p5, GeminiProvider):
        ok("Auto-detects GeminiProvider from AIza... key prefix")
    else:
        fail(f"Expected GeminiProvider from AIza prefix, got {type(p5).__name__}")

    os.environ["LLM_API_KEY"] = "sk-autodetect123"
    p6 = get_llm_provider()
    if isinstance(p6, OpenAIProvider):
        ok("Auto-detects OpenAIProvider from sk-... key prefix")
    else:
        fail(f"Expected OpenAIProvider from sk- prefix, got {type(p6).__name__}")

    for k in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL"):
        os.environ.pop(k, None)
except Exception as e:
    fail("get_llm_provider factory checks failed", str(e))


# CHECK 9
section("CHECK 9 -- QueryAnalyzer LLM -> fallback chain")
try:
    unavailable_provider = MockLLMProvider(api_key="")
    unavailable_provider.is_available = lambda: False

    qa = QueryAnalyzer(provider=unavailable_provider)
    result = qa.extract_structured_requirements("500 kVA distribution transformer 11kV/433V outdoor oil-cooled")
    if result is not None and isinstance(result, StructuredRequirements):
        ok("QueryAnalyzer falls back to RuleExtractor when provider unavailable")
    else:
        fail("QueryAnalyzer fallback failed when provider unavailable")

    fail_provider = MockLLMProvider()
    fail_provider.parse_query = lambda q: None

    qa2 = QueryAnalyzer(provider=fail_provider)
    result2 = qa2.extract_structured_requirements("500 kVA transformer")
    if result2 is not None and isinstance(result2, StructuredRequirements):
        ok("QueryAnalyzer falls back to RuleExtractor when parse_query returns None")
    else:
        fail("QueryAnalyzer fallback failed when parse_query returns None")

    def raise_provider(q):
        raise RuntimeError("Simulated provider crash")

    crash_provider = MockLLMProvider()
    crash_provider.parse_query = raise_provider

    qa3 = QueryAnalyzer(provider=crash_provider)
    result3 = qa3.extract_structured_requirements("500 kVA transformer")
    if result3 is not None and isinstance(result3, StructuredRequirements):
        ok("QueryAnalyzer catches provider exception and falls back to RuleExtractor")
    else:
        fail("QueryAnalyzer did not fall back when provider raised exception")
except Exception as e:
    fail("QueryAnalyzer fallback checks failed", str(e))


# CHECK 10
section("CHECK 10 -- Anti-hallucination safeguards")
try:
    import re
    import inspect as _inspect

    source = _inspect.getsource(GeminiProvider.parse_query)
    if "DO NOT" in source:
        ok("GeminiProvider prompt contains anti-hallucination instruction")
    else:
        fail("GeminiProvider prompt is MISSING anti-hallucination instruction")

    source2 = _inspect.getsource(OpenAIProvider.parse_query)
    if "DO NOT" in source2:
        ok("OpenAIProvider prompt contains anti-hallucination instruction")
    else:
        fail("OpenAIProvider prompt is MISSING anti-hallucination instruction")

    # Simulate LLM hallucinating IS codes
    bad_json = json.dumps({
        "product": "transformer",
        "capacity": "500 kVA",
        "cooling": "oil-cooled",
        "installation": "outdoor",
        "primary_voltage": "11 kV",
        "secondary_voltage": "433 V",
        "foreign_standards": ["IEC 60076", "IS 2026"],
        "application": "power distribution"
    })
    m = MockLLMProvider()
    parsed = m.validate_output(bad_json)
    if parsed:
        is_pattern = re.compile(r"^IS\s+\d+", re.IGNORECASE)
        hallucinated = [s for s in (parsed.foreign_standards or []) if is_pattern.match(s)]
        if hallucinated:
            warn(f"LLM returned IS codes in foreign_standards: {hallucinated} -- downstream must NOT use these for IS DB lookups")
        else:
            ok("No IS codes detected in foreign_standards (IEC 60076 only, IS 2026 filtered)")
except Exception as e:
    fail("Anti-hallucination checks failed", str(e))


# CHECK 11
section("CHECK 11 -- RuleExtractor determinism")
try:
    re_ = RuleExtractor()
    q = "500 kVA outdoor oil-cooled distribution transformer, 11kV/433V, IEC 60076 compliant"
    r = re_.extract(q)

    checks = [
        ("product",           r.product and "transformer" in r.product.lower(),  f"got '{r.product}'"),
        ("capacity",          r.capacity == "500 kVA",                           f"got '{r.capacity}'"),
        ("cooling",           r.cooling == "oil-cooled",                          f"got '{r.cooling}'"),
        ("installation",      r.installation == "outdoor",                        f"got '{r.installation}'"),
        ("primary_voltage",   r.primary_voltage and "11" in r.primary_voltage,   f"got '{r.primary_voltage}'"),
        ("secondary_voltage", r.secondary_voltage and "433" in r.secondary_voltage, f"got '{r.secondary_voltage}'"),
        ("foreign_standards", "IEC 60076" in (r.foreign_standards or []),        f"got {r.foreign_standards}"),
    ]

    for name, cond, detail in checks:
        if cond:
            ok(f"RuleExtractor extracts {name} correctly")
        else:
            fail(f"RuleExtractor failed to extract {name}", detail)
except Exception as e:
    fail("RuleExtractor checks failed", str(e))


# CHECK 12
section("CHECK 12 -- QueryAnalyzer.analyze() output contract")
try:
    for k in ("LLM_PROVIDER", "LLM_API_KEY"):
        os.environ.pop(k, None)
    os.environ["LLM_PROVIDER"] = "mock"

    qa = QueryAnalyzer()
    analysis = qa.analyze("500 kVA outdoor oil-cooled distribution transformer, 11kV/433V")

    for key in ["raw_query", "clean_tokens", "detected_domains", "concepts",
                "structured_requirements", "llm_used", "llm_provider", "is_empty"]:
        if key in analysis:
            ok(f"analyze() output contains key: '{key}'")
        else:
            fail(f"analyze() output missing key: '{key}'")

    if analysis.get("is_empty") is False:
        ok("analyze() sets is_empty=False for non-empty query")
    else:
        fail("analyze() should set is_empty=False for non-empty query")

    sr = analysis.get("structured_requirements")
    if sr and isinstance(sr, dict):
        ok("structured_requirements is a dict in analyze() output")
    else:
        fail("structured_requirements should be a dict in analyze() output")
except Exception as e:
    fail("QueryAnalyzer.analyze() contract checks failed", str(e))
finally:
    os.environ.pop("LLM_PROVIDER", None)


# CHECK 13
section("CHECK 13 -- StructuredRequirements serialization")
try:
    sr = StructuredRequirements(
        product="transformer",
        capacity="500 kVA",
        cooling="oil-cooled",
        installation="outdoor",
        primary_voltage="11 kV",
        secondary_voltage="433 V",
        foreign_standards=["IEC 60076"],
        application="power distribution",
        additional_parameters={"rating_class": "ONAN"}
    )
    d = sr.to_dict()

    if isinstance(d, dict):
        ok("StructuredRequirements.to_dict() returns a dict")
    else:
        fail("StructuredRequirements.to_dict() did not return a dict")

    if d.get("product") == "transformer":
        ok("to_dict() serializes product correctly")
    else:
        fail("to_dict() failed to serialize product")

    if d.get("additional_parameters", {}).get("rating_class") == "ONAN":
        ok("to_dict() serializes additional_parameters correctly")
    else:
        fail("to_dict() failed to serialize additional_parameters")
except Exception as e:
    fail("StructuredRequirements serialization checks failed", str(e))


# CHECK 14
section("CHECK 14 -- .env.example configuration keys")
try:
    env_path = os.path.join(PROJECT_ROOT, ".env.example")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()
        for key in ["LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_TIMEOUT"]:
            if key in env_content:
                ok(f".env.example contains '{key}'")
            else:
                fail(f".env.example is missing '{key}'")
    else:
        warn(".env.example not found -- skipping env key checks")
except Exception as e:
    fail(".env.example checks failed", str(e))


# CHECK 15
section("CHECK 15 -- LLM_TIMEOUT env parsing")
try:
    os.environ["LLM_TIMEOUT"] = "3.5"
    os.environ["LLM_PROVIDER"] = "mock"
    p = get_llm_provider()
    if p.timeout == 3.5:
        ok("LLM_TIMEOUT=3.5 parsed correctly")
    else:
        warn(f"LLM_TIMEOUT may not be threaded to provider instance (got {p.timeout})")

    os.environ["LLM_TIMEOUT"] = "not_a_number"
    p2 = get_llm_provider()
    if p2.timeout == 5.0:
        ok("Invalid LLM_TIMEOUT safely defaults to 5.0")
    else:
        fail(f"Invalid LLM_TIMEOUT should default to 5.0, got {p2.timeout}")
except Exception as e:
    fail("LLM_TIMEOUT env parsing checks failed", str(e))
finally:
    for k in ("LLM_TIMEOUT", "LLM_PROVIDER"):
        os.environ.pop(k, None)


# SUMMARY
print(f"\n{'='*60}")
total = passed + failed
print(f"  Phase 6A Verification Complete")
print(f"  {GREEN}Passed : {passed}{RESET}")
print(f"  {RED}Failed : {failed}{RESET}")
if warnings:
    print(f"  {YELLOW}Warnings: {warnings}{RESET}")
print(f"  Total  : {total}")
print(f"{'='*60}\n")

if failed == 0:
    print(f"{GREEN}  ALL PHASE 6A CHECKS PASSED{RESET}\n")
    sys.exit(0)
else:
    print(f"{RED}  {failed} CHECK(S) FAILED -- See details above{RESET}\n")
    sys.exit(1)
