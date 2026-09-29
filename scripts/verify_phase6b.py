"""
Phase 6B Verification Suite - Real BGE-M3 Embeddings + IN_MEMORY Retrieval
Tests:
  1.  sentence-transformers installed
  2.  BGE-M3 model identifier configured
  3.  HF_HOME is on E: drive (not C:)
  4.  BGE-M3 model loads from EmbeddingService
  5.  Real embedding generated (not DEMO_FALLBACK)
  6.  Embedding dimension is 1024
  7.  Embeddings are unit-normalized
  8.  EmbeddingService provider_name == REAL_BGE_M3
  9.  EmbeddingService is_fallback == False
  10. IN_MEMORY retrieval mode active (Qdrant intentionally absent)
  11. 21 verified standards remain available
  12. Transformer query produces results (no fabricated standards)
  13. retrieval_mode == IN_MEMORY in live pipeline
  14. embedding_mode == REAL_BGE_M3 in live pipeline
  15. Reranker weights unchanged (40/20/20/20)
  16. Phase 6A Gemini integration still works or falls back safely
  17. No fabricated IS codes introduced
  18. All recommendations originate from verified catalogue
"""
import os, sys, math, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
except ImportError:
    pass

PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0

def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  PASS  {msg}")

def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"  FAIL  {msg}")

def warn(msg):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"  WARN  {msg}")

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

def load_verified_catalogue():
    for rel in ["data/real/standards_catalogue.json", "data/standards_catalogue.json"]:
        p = ROOT / rel
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {s["standard_number"] for s in data}
    return set()

section("CHECK 1 -- sentence-transformers installed")
try:
    import sentence_transformers
    ok(f"sentence-transformers installed: {sentence_transformers.__version__}")
except ImportError as e:
    fail(f"sentence-transformers not installed: {e}")

section("CHECK 2 -- BGE-M3 model identifier configured")
model_id = os.getenv("EMBEDDING_MODEL", "")
if model_id == "BAAI/bge-m3":
    ok(f"EMBEDDING_MODEL={model_id}")
elif model_id:
    warn(f"EMBEDDING_MODEL={model_id} (expected BAAI/bge-m3)")
else:
    fail("EMBEDDING_MODEL not set in environment")

section("CHECK 3 -- HF_HOME on E: drive")
hf_home = os.getenv("HF_HOME", "")
if hf_home:
    if hf_home.lower().startswith("e:"):
        ok(f"HF_HOME={hf_home} (on E: drive)")
    else:
        fail(f"HF_HOME={hf_home} -- NOT on E:, model may fill C:")
else:
    fail("HF_HOME not configured -- model would download to C: (default)")

section("CHECK 4 -- EmbeddingService loads BGE-M3")
embedding_service = None
try:
    from ai_engine.embeddings.embedding_service import EmbeddingService
    embedding_service = EmbeddingService(force_provider="bge-m3")
    if not embedding_service.is_fallback:
        ok("EmbeddingService initialized with REAL_BGE_M3 provider")
    else:
        fail(f"EmbeddingService using fallback: {embedding_service.provider_name}")
except Exception as e:
    fail(f"EmbeddingService initialization error: {e}")

section("CHECK 5 -- Real embedding generated")
test_vec = None
if embedding_service and not embedding_service.is_fallback:
    try:
        test_vec = embedding_service.embed_text("500 kVA distribution transformer")
        ok(f"embed_text returned vector of length {len(test_vec)}")
    except Exception as e:
        fail(f"embed_text error: {e}")
else:
    fail("Skipped -- EmbeddingService not initialized with real provider")

section("CHECK 6 -- Embedding dimension is 1024")
if test_vec is not None:
    dim = len(test_vec)
    if dim == 1024:
        ok(f"Embedding dimension: {dim}")
    else:
        fail(f"Embedding dimension: {dim} (expected 1024)")
else:
    fail("Skipped -- no vector to check")

section("CHECK 7 -- Embeddings are unit-normalized")
if test_vec is not None:
    norm = math.sqrt(sum(x * x for x in test_vec))
    if abs(norm - 1.0) < 1e-4:
        ok(f"Vector norm: {norm:.6f} (unit-normalized)")
    else:
        fail(f"Vector norm: {norm:.6f} (expected ~1.0)")
else:
    fail("Skipped -- no vector to check")

section("CHECK 8 -- EmbeddingService provider_name == REAL_BGE_M3")
if embedding_service:
    pname = embedding_service.provider_name
    if pname == "REAL_BGE_M3":
        ok(f"provider_name: {pname}")
    else:
        fail(f"provider_name: {pname} (expected REAL_BGE_M3)")
else:
    fail("Skipped -- EmbeddingService not initialized")

section("CHECK 9 -- EmbeddingService is_fallback == False")
if embedding_service:
    if not embedding_service.is_fallback:
        ok("is_fallback: False")
    else:
        fail("is_fallback: True (still DEMO_FALLBACK)")
else:
    fail("Skipped -- EmbeddingService not initialized")

section("CHECK 10 -- IN_MEMORY retrieval mode (Qdrant intentionally absent)")
try:
    from ai_engine.vector_db.qdrant_service import QdrantService
    qdrant_svc = QdrantService(url="http://localhost:6333")
    mode = qdrant_svc.retrieval_mode
    if mode == "IN_MEMORY":
        ok(f"retrieval_mode: {mode} (Qdrant absent -- expected behaviour)")
    elif mode == "QDRANT":
        ok(f"retrieval_mode: {mode} (live Qdrant connected -- also valid)")
    else:
        fail(f"retrieval_mode: {mode}")
except Exception as e:
    fail(f"QdrantService init error: {e}")

section("CHECK 11 -- 21 verified standards available")
try:
    from ai_engine.ingestion.manual_json_connector import ManualJsonConnector
    connector = ManualJsonConnector()
    standards = connector.fetch_standards()
    count = len(standards)
    if count >= 21:
        ok(f"Verified standards loaded: {count}")
    else:
        fail(f"Only {count} standards loaded (expected 21)")
except Exception as e:
    fail(f"Standards load error: {e}")

section("CHECK 12 -- Full pipeline: transformer query produces results")
pipeline_result = None
try:
    from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline
    pipeline = RecommendationPipeline()
    query = "500 kVA outdoor oil-cooled distribution transformer, 11kV/433V, IEC 60076 compliant"
    pipeline_result = pipeline.run_query_pipeline(query, limit=5)
    recs = pipeline_result.get("recommendations", [])
    if recs:
        ok(f"Pipeline returned {len(recs)} recommendations for transformer query")
    else:
        fail("Pipeline returned 0 recommendations")
except Exception as e:
    fail(f"Pipeline error: {e}")

section("CHECK 13 -- retrieval_mode in live pipeline")
if pipeline_result:
    rm = pipeline_result.get("retrieval_mode", "")
    if rm in ("IN_MEMORY", "QDRANT"):
        ok(f"retrieval_mode: {rm}")
    else:
        fail(f"retrieval_mode: {rm!r} (unexpected value)")
else:
    fail("Skipped -- no pipeline result")

section("CHECK 14 -- embedding_mode == REAL_BGE_M3 in live pipeline")
if pipeline_result:
    em = pipeline_result.get("embedding_mode", "")
    if em == "REAL_BGE_M3":
        ok(f"embedding_mode: {em}")
    else:
        fail(f"embedding_mode: {em!r} (expected REAL_BGE_M3)")
else:
    fail("Skipped -- no pipeline result")

section("CHECK 15 -- Reranker weights unchanged (40/20/20/20)")
try:
    from ai_engine.reranker.reranker import Reranker
    r = Reranker()
    w = r.weights
    expected = {"semantic": 0.40, "material": 0.20, "environment": 0.20, "technical_alignment": 0.20}
    if w == expected:
        ok(f"Reranker weights: {w}")
    else:
        fail(f"Reranker weights changed: {w} (expected {expected})")
except Exception as e:
    fail(f"Reranker check error: {e}")

section("CHECK 16 -- Phase 6A Gemini integration works or falls back safely")
try:
    from ai_engine.query.llm_provider import get_llm_provider
    provider = get_llm_provider()
    pname = provider.__class__.__name__
    avail = provider.is_available()
    ok(f"LLM provider: {pname}  is_available={avail}")
    if avail:
        result = provider.parse_query("10 mm2 copper conductor PVC insulated cable")
        if result is not None:
            ok("Gemini parse_query returned structured requirements")
        else:
            warn("Gemini parse_query returned None (quota/network -- RuleExtractor fallback active)")
    else:
        warn(f"LLM provider {pname} not available -- RuleExtractor fallback active")
except Exception as e:
    fail(f"LLM provider check error: {e}")

section("CHECK 17 -- No fabricated IS codes in pipeline output")
verified_catalogue = load_verified_catalogue()
if pipeline_result and verified_catalogue:
    recs = pipeline_result.get("recommendations", [])
    fabricated = [r.get("standard_number") for r in recs
                  if r.get("standard_number") and r.get("standard_number") not in verified_catalogue]
    if not fabricated:
        ok(f"No fabricated IS codes in {len(recs)} recommendations")
    else:
        fail(f"Fabricated IS codes detected: {fabricated}")
elif not verified_catalogue:
    warn("Could not load verified catalogue for anti-hallucination check")
else:
    fail("Skipped -- no pipeline result")

section("CHECK 18 -- All recommendations from verified catalogue")
if pipeline_result and verified_catalogue:
    recs = pipeline_result.get("recommendations", [])
    outside = [r.get("standard_number") for r in recs
               if r.get("standard_number") and r.get("standard_number") not in verified_catalogue]
    if not outside:
        ok(f"All {len(recs)} recommendations originate from verified catalogue")
    else:
        fail(f"Standards outside verified catalogue: {outside}")
else:
    fail("Skipped -- missing pipeline result or catalogue")

total = PASS_COUNT + FAIL_COUNT + WARN_COUNT
print(f"\n{'='*60}")
print(f"  Phase 6B Verification Complete")
print(f"  Passed   : {PASS_COUNT}")
print(f"  Failed   : {FAIL_COUNT}")
print(f"  Warnings : {WARN_COUNT}")
print(f"  Total    : {total}")
print(f"{'='*60}")
if FAIL_COUNT == 0:
    print(f"\n  ALL PHASE 6B CHECKS PASSED\n")
    sys.exit(0)
else:
    print(f"\n  {FAIL_COUNT} CHECK(S) FAILED -- see above\n")
    sys.exit(1)
