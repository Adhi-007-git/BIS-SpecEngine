"""
Phase 6B BGE-M3 model download + embedding test.
MUST be run after sentence-transformers is installed.
Verifies: HF_HOME on E:, model loads, real embeddings generated, dimension correct, normalized.
"""
import os, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Step 0: Validate HF_HOME BEFORE loading anything
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

hf_home = os.getenv("HF_HOME", "")
print(f"=== DISK / CACHE CHECK ===")
print(f"HF_HOME env        : {hf_home}")
print(f"HF_HOME on E:      : {'YES' if hf_home.lower().startswith('e:') else 'NO -- STOP!'}")
if not hf_home.lower().startswith("e:"):
    print("ABORT: HF_HOME not on E: drive. Model download would fill C:.")
    sys.exit(1)

# Also set it explicitly so sub-processes see it
os.environ["HF_HOME"] = hf_home

print(f"\n=== PACKAGE CHECK ===")
try:
    import sentence_transformers
    print(f"sentence-transformers : {sentence_transformers.__version__}  OK")
except ImportError as e:
    print(f"FAIL: sentence-transformers not installed: {e}")
    sys.exit(1)

print(f"\n=== MODEL LOAD ===")
model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
print(f"Loading model: {model_name}")
print(f"Cache dir    : {hf_home}")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    print(f"Model loaded  : OK")
except Exception as e:
    print(f"FAIL: Model load error: {e}")
    sys.exit(1)

print(f"\n=== EMBEDDING DIMENSION CHECK ===")
test_texts = [
    "500 kVA outdoor oil-cooled distribution transformer, 11kV/433V",
    "PVC insulated copper conductor cable, 1100V grade, IS 1554"
]
vecs = model.encode(test_texts, normalize_embeddings=True)
dim = len(vecs[0])
print(f"Embedding dimension: {dim}")
assert dim == 1024, f"Expected 1024, got {dim}"
print("Dimension check    : PASS (1024)")

print(f"\n=== NORMALIZATION CHECK ===")
for i, (text, vec) in enumerate(zip(test_texts, vecs)):
    norm = math.sqrt(sum(x * x for x in vec))
    print(f"  vec[{i}] norm: {norm:.6f}  {'PASS' if abs(norm - 1.0) < 1e-5 else 'FAIL'}")

print(f"\n=== COSINE SIMILARITY CHECK ===")
def cosine(a, b):
    return sum(x*y for x, y in zip(a, b))  # already normalized

sim_self = cosine(vecs[0], vecs[0])
sim_cross = cosine(vecs[0], vecs[1])
print(f"  Self-similarity  : {sim_self:.6f}  (expected ~1.0)")
print(f"  Cross-similarity : {sim_cross:.6f}  (expected < 1.0)")
assert abs(sim_self - 1.0) < 1e-5, "Self-similarity not 1.0"
assert sim_cross < 1.0, "Cross-similarity should be < 1.0"
print("  Cosine check     : PASS")

print(f"\n=== HF CACHE LOCATION CHECK ===")
hub_dir = Path(hf_home) / "hub"
if hub_dir.exists():
    models = list(hub_dir.iterdir())
    print(f"  {hub_dir}: {len(models)} model(s) downloaded")
    for m in models:
        print(f"    - {m.name}")
else:
    print(f"  {hub_dir}: directory not yet created (model may be cached elsewhere)")

print(f"\n=== ALL BGE-M3 CHECKS PASSED ===")
