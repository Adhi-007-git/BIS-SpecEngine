"""
Graph Builder: Converts standard relationships into React Flow compatible
nodes and edges for the frontend interactive knowledge graph visualization.
"""
from typing import Dict, Any, List

class GraphBuilder:
    """Transforms standard entities and relations into graph visual layouts."""

    def build_flow_graph(self, primary_standard: Dict[str, Any], related_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates {nodes: [...], edges: [...]} for React Flow."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        std_num = primary_standard.get("standard_number", "IS-STANDARD")
        title = primary_standard.get("title", "")

        # Center root node
        nodes.append({
            "id": "root",
            "type": "input",
            "position": {"x": 350, "y": 200},
            "data": {
                "label": f"⭐ {std_num}\n{title[:40]}...",
                "standard_number": std_num,
                "node_type": "PRIMARY_STANDARD",
                "status": primary_standard.get("status", "Active")
            },
            "style": {
                "background": "#1e293b",
                "color": "#f8fafc",
                "border": "2px solid #3b82f6",
                "borderRadius": "8px",
                "padding": "12px",
                "width": 240
            }
        })

        # Calculate radial or tiered positions for related standards
        angles = [-60, -20, 20, 60, 100, 140, 180, 220]
        for idx, item in enumerate(related_items):
            node_id = f"rel_{idx + 1}"
            rel_type = item.get("relation", "NORMATIVE_REFERENCE")
            item_num = item.get("standard_number", f"REF-{idx+1}")
            item_title = item.get("title", "")

            # Determine colors based on relationship
            if rel_type == "REQUIRES_TESTING_VIA":
                border_color = "#10b981" # Emerald
                bg_color = "#064e3b"
            elif rel_type == "MANDATED_BY":
                border_color = "#f59e0b" # Amber
                bg_color = "#78350f"
            elif rel_type == "SUPERSEDES":
                border_color = "#ef4444" # Rose
                bg_color = "#4c0519"
            elif rel_type == "SPECIFIES_MATERIAL":
                border_color = "#06b6d4" # Cyan
                bg_color = "#083344"
            elif rel_type == "GOVERNED_BY_SAFETY":
                border_color = "#a855f7" # Purple
                bg_color = "#3b0764"
            else:
                border_color = "#6366f1" # Indigo
                bg_color = "#1e1b4b"

            # Position in columns
            col_x = 750 if idx % 2 == 0 else 50
            row_y = 60 + (idx * 110)

            nodes.append({
                "id": node_id,
                "type": "default",
                "position": {"x": col_x, "y": row_y},
                "data": {
                    "label": f"{item_num}\n{item_title[:35]}...",
                    "standard_number": item_num,
                    "node_type": rel_type
                },
                "style": {
                    "background": bg_color,
                    "color": "#f8fafc",
                    "border": f"2px solid {border_color}",
                    "borderRadius": "8px",
                    "padding": "10px",
                    "width": 220,
                    "fontSize": "12px"
                }
            })

            edges.append({
                "id": f"edge_root_{node_id}",
                "source": "root" if rel_type != "MANDATED_BY" else node_id,
                "target": node_id if rel_type != "MANDATED_BY" else "root",
                "label": rel_type.replace("_", " "),
                "animated": rel_type in ("REQUIRES_TESTING_VIA", "GOVERNED_BY_SAFETY"),
                "style": {"stroke": border_color, "strokeWidth": 2}
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
