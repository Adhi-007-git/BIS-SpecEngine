import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline
pipeline = RecommendationPipeline()

standards = pipeline.search_engine.get_all_standards()
print(f"Total standards indexed: {len(standards)}")

isolated_standards = []

for s in standards:
    num = s.get("standard_number")
    title = s.get("title", "")
    details = pipeline.get_standard_details(num)
    graph = details.get("graph", {})
    nodes = graph.get("total_nodes", 0)
    edges = graph.get("total_edges", 0)
    related = details.get("related_standards", [])
    print(f"{num:25} | nodes={nodes:2} | edges={edges:2} | related_count={len(related):2} | title={title[:40]}")
    if edges == 0:
        isolated_standards.append((num, title, nodes, edges))

print("\n" + "=" * 60)
print(f"STANDARDS WITH NO VERIFIED RELATIONSHIPS (edges == 0): {len(isolated_standards)}")
print("=" * 60)
for num, title, nodes, edges in isolated_standards:
    print(f"Code: {num}")
    print(f"Title: {title}")
    print(f"Nodes: {nodes}, Edges: {edges}\n")
