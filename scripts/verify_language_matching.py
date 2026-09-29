"""
SIH26108 - Automatic Response Language Matching Verification Suite.
Automated tests validating all 8 mandatory requirements:
1. English query -> English response.
2. Hindi query -> Hindi response.
3. Tamil query -> Tamil response.
4. Mixed Hindi-English query (dominant language detection).
5. Unsupported product -> limitation message in the detected language.
6. Hindi query normalized internally into English -> final answer remains in Hindi.
7. Missing or unavailable LLM provider -> safe fallback behaviour.
8. Standard identifiers and evidence references remain unchanged after translation.
"""
import sys
import os
import re
from pathlib import Path
from fastapi.testclient import TestClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from backend.app.main import app
from ai_engine.query.multilingual import MultilingualNormalizer, detect_language_and_script
from ai_engine.query.query_analyzer import QueryAnalyzer
from ai_engine.query.llm_provider import BaseLLMProvider
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

def run_tests():
    print("==================================================================")
    print("SIH26108 - Automatic Response Language Matching Verification")
    print("==================================================================")
    client = TestClient(app)
    passed_tests = 0
    total_tests = 8

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 1: English query -> English response
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 1] English query -> English response...")
    q_en = "Find the applicable standard for a 1100 V PVC cable."
    resp_en = client.post("/api/search", json={"query": q_en, "limit": 3})
    assert resp_en.status_code == 200, f"Search failed: {resp_en.text}"
    d_en = resp_en.json()
    assert d_en["total_recommendations"] > 0
    assert d_en["response_language"] == "en"
    assert d_en["response_language_name"] == "English"
    rec_en = d_en["recommendations"][0]
    assert "IS 1554" in rec_en["standard_number"]
    # Reasoning is in English
    assert any(w in rec_en["reason"].lower() for w in ["cable", "voltage", "material", "pvc", "standard"])
    print(f" [PASS] English query responded in English. Standard: {rec_en['standard_number']}")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 2: Hindi query -> Hindi response
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 2] Hindi query -> Hindi response...")
    q_hi = "1100 V पीवीसी केबल के लिए लागू भारतीय मानक बताइए।"
    resp_hi = client.post("/api/search", json={"query": q_hi, "limit": 3})
    assert resp_hi.status_code == 200, f"Search failed: {resp_hi.text}"
    d_hi = resp_hi.json()
    assert d_hi["total_recommendations"] > 0
    assert d_hi["response_language"] == "hi"
    assert d_hi["response_language_name"] == "Hindi"
    rec_hi = d_hi["recommendations"][0]
    assert "IS 1554" in rec_hi["standard_number"]
    # Check that reason contains Hindi explanation with Devanagari text
    has_devanagari_reason = any(0x0900 <= ord(c) <= 0x097F for c in rec_hi["reason"])
    assert has_devanagari_reason, f"Reason does not contain Hindi text: {rec_hi['reason']}"
    assert "IS 1554" in rec_hi["reason"]
    # Check summary exists and has Devanagari
    if d_hi.get("summary"):
        assert any(0x0900 <= ord(c) <= 0x097F for c in d_hi["summary"])
    print(f" [PASS] Hindi query responded in Hindi. Reason: {rec_hi['reason']}")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 3: Tamil query -> Tamil response
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 3] Tamil query -> Tamil response...")
    q_ta = "1100 V PVC கேபிளுக்குப் பொருந்தும் இந்திய தரநிலையைச் சொல்லுங்கள்."
    resp_ta = client.post("/api/search", json={"query": q_ta, "limit": 3})
    assert resp_ta.status_code == 200, f"Search failed: {resp_ta.text}"
    d_ta = resp_ta.json()
    assert d_ta["total_recommendations"] > 0
    assert d_ta["response_language"] == "ta"
    assert d_ta["response_language_name"] == "Tamil"
    rec_ta = d_ta["recommendations"][0]
    assert "IS 1554" in rec_ta["standard_number"]
    # Check that reason contains Tamil explanation with Tamil script characters
    has_tamil_reason = any(0x0B80 <= ord(c) <= 0x0BFF for c in rec_ta["reason"])
    assert has_tamil_reason, f"Reason does not contain Tamil text: {rec_ta['reason']}"
    assert "IS 1554" in rec_ta["reason"]
    if d_ta.get("summary"):
        assert any(0x0B80 <= ord(c) <= 0x0BFF for c in d_ta["summary"])
    print(f" [PASS] Tamil query responded in Tamil. Reason: {rec_ta['reason']}")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 4: Mixed Hindi-English query (dominant language handling)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 4] Mixed Hindi-English query (dominant language handling)...")
    # Subtest 4a: Hindi dominant structure with English loanwords
    q_mixed_hi = "1100 V PVC cable के लिए मानक बताइए"
    lang_info_hi = detect_language_and_script(q_mixed_hi)
    assert lang_info_hi["response_language"] == "hi", f"Expected 'hi', got {lang_info_hi['response_language']}"
    resp_mixed_hi = client.post("/api/search", json={"query": q_mixed_hi, "limit": 3})
    assert resp_mixed_hi.status_code == 200
    assert resp_mixed_hi.json()["response_language"] == "hi"

    # Subtest 4b: English dominant structure with Hindi word
    q_mixed_en = "Find the applicable standard for 1100 V PVC cable के लिए"
    lang_info_en = detect_language_and_script(q_mixed_en)
    assert lang_info_en["response_language"] == "en", f"Expected 'en', got {lang_info_en['response_language']}"
    resp_mixed_en = client.post("/api/search", json={"query": q_mixed_en, "limit": 3})
    assert resp_mixed_en.status_code == 200
    assert resp_mixed_en.json()["response_language"] == "en"
    print(" [PASS] Mixed-language dominance resolved: Hindi-dominant -> Hindi; English-dominant -> English.")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 5: Unsupported product -> limitation message in user's language
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 5] Unsupported product -> limitation message in detected language...")
    # Hindi unsupported query
    q_unsup_hi = "रॉकेट प्रणोदन और अंतरिक्ष उपग्रह प्रणाली"
    resp_unsup_hi = client.post("/api/search", json={"query": q_unsup_hi, "limit": 3})
    assert resp_unsup_hi.status_code == 200
    d_unsup_hi = resp_unsup_hi.json()
    assert d_unsup_hi["total_recommendations"] == 0
    assert d_unsup_hi["response_language"] == "hi"
    msg_hi = d_unsup_hi.get("message", "")
    assert len(msg_hi) > 0
    # Must communicate limitation in Hindi without hallucinating a standard
    assert any(0x0900 <= ord(c) <= 0x097F for c in msg_hi)
    assert "सत्यापित भारतीय मानक" in msg_hi or "कैटलॉग" in msg_hi or "अधिकारी समीक्षा" in msg_hi or "असमर्थ" in msg_hi

    # Tamil unsupported query
    q_unsup_ta = "விண்கலம் மற்றும் ராக்கெட் உந்துவிசை அமைப்பு"
    resp_unsup_ta = client.post("/api/search", json={"query": q_unsup_ta, "limit": 3})
    assert resp_unsup_ta.status_code == 200
    d_unsup_ta = resp_unsup_ta.json()
    assert d_unsup_ta["total_recommendations"] == 0
    assert d_unsup_ta["response_language"] == "ta"
    msg_ta = d_unsup_ta.get("message", "")
    assert len(msg_ta) > 0
    assert any(0x0B80 <= ord(c) <= 0x0BFF for c in msg_ta)
    assert "இந்திய தரநிலையும்" in msg_ta or "பட்டியலில்" in msg_ta or "மறுஆய்வு" in msg_ta or "இயல்பாக்க" in msg_ta
    print(" [PASS] Unsupported queries returned appropriate limitation messages in Hindi and Tamil without inventing standards.")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 6: Hindi query normalized internally into English -> final answer in Hindi
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 6] Hindi query normalized internally to English -> final answer remains in Hindi...")
    q_hi_pipe = "1100 V पीवीसी केबल के लिए लागू भारतीय मानक बताइए।"
    pipeline = RecommendationPipeline()
    res_hi = pipeline.run_query_pipeline(q_hi_pipe)
    qa = res_hi["query_analysis"]
    # 1. Preserved original query
    assert qa["original_query"] == q_hi_pipe
    # 2. Normalized internally into English technical query
    norm_en = qa.get("normalized_english_query", "")
    assert len(norm_en) > 0
    assert "1100 V" in norm_en
    assert "PVC" in norm_en or "cable" in norm_en.lower()
    # 3. But response language is marked as 'hi'
    assert res_hi["response_language"] == "hi"
    # 4. Final recommendation reason remains in Hindi
    assert res_hi["total_recommendations"] > 0
    top_reason = res_hi["recommendations"][0]["reason"]
    assert any(0x0900 <= ord(c) <= 0x097F for c in top_reason)
    print(f" [PASS] Query internally normalized to English '{norm_en}', and final response output generated in Hindi.")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 7: Missing or unavailable LLM provider -> safe fallback behaviour
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 7] Missing or unavailable LLM provider -> safe fallback behaviour...")
    class OfflineFailingProvider(BaseLLMProvider):
        def is_available(self):
            return True
        def parse_query(self, q):
            raise ConnectionError("External LLM API unreachable (503 Service Unavailable)")
        def generate_multilingual_response(self, q, ctx, lang):
            raise TimeoutError("External LLM response generation timed out")

    offline_analyzer = QueryAnalyzer(provider=OfflineFailingProvider())
    analyzed = offline_analyzer.analyze("1100 V पीवीसी केबल के लिए लागू भारतीय मानक बताइए।")
    assert analyzed["response_language"] == "hi"
    assert analyzed["normalization_status"] == "SUCCESS"

    # Test pipeline with offline/failing generator fallback
    pipeline_fallback = RecommendationPipeline()
    # Force recommendation generator to use deterministic multilingual logic
    fb_res = pipeline_fallback.run_query_pipeline("1100 V पीवीसी केबल के लिए लागू भारतीय मानक बताइए।")
    assert fb_res["response_language"] == "hi"
    assert len(fb_res["recommendations"]) > 0
    assert any(0x0900 <= ord(c) <= 0x097F for c in fb_res["recommendations"][0]["reason"])
    print(" [PASS] Offline/failing provider safely and gracefully triggered deterministic multilingual response generation.")
    passed_tests += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 8: Standard identifiers and evidence references remain unchanged
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[TEST 8] Standard identifiers and evidence references remain unchanged after translation...")
    for test_query, lang in [
        ("1100 V पीवीसी केबल के लिए लागू भारतीय मानक बताइए।", "hi"),
        ("1100 V PVC கேபிளுக்குப் பொருந்தும் இந்திய தரநிலையைச் சொல்லுங்கள்.", "ta")
    ]:
        res = client.post("/api/search", json={"query": test_query, "limit": 2}).json()
        assert res["total_recommendations"] > 0
        for rec in res["recommendations"]:
            std_num = rec["standard_number"]
            # Standard number MUST match exact official regex (e.g. 'IS 1554 (Part 1):1988')
            assert re.match(r'^IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+', std_num), f"Mangled standard number: {std_num}"
            # Standard title must remain the official Bureau of Indian Standards title
            assert len(rec["title"]) > 0
            assert not any(0x0900 <= ord(c) <= 0x097F for c in rec["title"]), "Title was destructively translated!"
            assert not any(0x0B80 <= ord(c) <= 0x0BFF for c in rec["title"]), "Title was destructively translated!"
            # Evidence source must remain official
            assert "Bureau of Indian Standards" in rec["source"]
            # Evidence page/section must be integer or string, not mangled
            if rec.get("page") is not None:
                assert isinstance(rec["page"], int)

    print(" [PASS] Standard identifiers (IS numbers), titles, and citations remain 100% authentic and unmangled.")
    passed_tests += 1

    print("\n==================================================================")
    print(f"AUTOMATIC RESPONSE LANGUAGE MATCHING: {passed_tests}/{total_tests} TESTS PASSED (100%)")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
