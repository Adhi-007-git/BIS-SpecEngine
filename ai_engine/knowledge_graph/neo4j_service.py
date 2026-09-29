"""
Neo4j Knowledge Graph Service: Manages relationships between Indian Standards,
testing methods, normative references, supersessions, and Quality Control Orders (QCOs).
Includes transparent in-memory graph fallback for zero-dependency dev mode.
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    """Provides Cypher queries and standard relationship graph lookups."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "sih_password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._is_live = False
        self._memory_graph: Dict[str, Dict[str, Any]] = {}
        self._init_driver()

    def _init_driver(self):
        """Attempts connection to Neo4j instance."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password), connection_timeout=2.0)
            self.driver.verify_connectivity()
            self._is_live = True
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            self.driver = None
            self._is_live = False
            logger.warning(f"Neo4j not reachable at {self.uri} ({e}). Using in-memory graph fallback.")

    def is_connected(self) -> bool:
        return self._is_live

    def register_standard_node(self, standard_data: Dict[str, Any]):
        """Caches standard in graph store."""
        std_num = standard_data.get("standard_number")
        if not std_num:
            return

        if self._is_live and self.driver:
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MERGE (s:Standard {number: $num})
                        SET s.title = $title, s.status = $status
                        """,
                        num=std_num,
                        title=standard_data.get("title", ""),
                        status=standard_data.get("status", "")
                    )
            except Exception as e:
                logger.error(f"Error registering standard to Neo4j: {e}")

        # In-memory store
        self._memory_graph[std_num] = standard_data

    def get_related_standards(self, standard_number: str) -> List[Dict[str, Any]]:
        """Retrieves normative references, test methods, and superseding standards."""
        if self._is_live and self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(
                        """
                        MATCH (s:Standard {number: $num})-[r]->(target:Standard)
                        RETURN target.number AS number, target.title AS title, type(r) AS relation
                        """,
                        num=standard_number
                    )
                    records = [{"standard_number": rec["number"], "title": rec["title"], "relation": rec["relation"]} for rec in result]
                    if records:
                        return records
            except Exception as e:
                logger.error(f"Neo4j query error: {e}")

        # Fallback to in-memory graph
        item = self._memory_graph.get(standard_number)
        if not item:
            # Fuzzy check
            for key, val in self._memory_graph.items():
                if standard_number.lower() in key.lower():
                    item = val
                    break

        if not item:
            return []

        related: List[Dict[str, Any]] = []
        seen_keys = set()

        def add_related(num: Optional[str], title: Optional[str], relation: str):
            if not num:
                return
            num_clean = str(num).strip()
            dedup_key = (num_clean.lower(), relation)
            if dedup_key in seen_keys or num_clean.lower() == standard_number.strip().lower():
                return
            seen_keys.add(dedup_key)
            related.append({
                "standard_number": num_clean,
                "title": title or self._get_title_for_standard(num_clean) or f"Referenced: {num_clean}",
                "relation": relation
            })

        # 1. Normative References
        for ref in item.get("normative_references", []):
            if isinstance(ref, dict):
                add_related(
                    ref.get("standard_number"),
                    ref.get("title"),
                    ref.get("relation", "NORMATIVE_REFERENCE")
                )
            elif isinstance(ref, str):
                add_related(ref, None, "NORMATIVE_REFERENCE")

        # 2. Test Methods
        for tm in item.get("test_methods", []):
            if isinstance(tm, dict):
                add_related(
                    tm.get("standard_number"),
                    tm.get("title"),
                    tm.get("relation", "REQUIRES_TESTING_VIA")
                )
            elif isinstance(tm, str):
                add_related(tm, None, "REQUIRES_TESTING_VIA")

        # 3. Superseding Standards
        if item.get("supersedes"):
            add_related(
                item.get("supersedes"),
                f"Preceding revision superseded by {item.get('standard_number')}",
                "SUPERSEDES"
            )

        # 4. Material Specifications (if explicitly represented in data)
        for mat in item.get("material_standards", []):
            if isinstance(mat, dict):
                add_related(
                    mat.get("standard_number"),
                    mat.get("title"),
                    mat.get("relation", "SPECIFIES_MATERIAL")
                )
            elif isinstance(mat, str):
                add_related(mat, None, "SPECIFIES_MATERIAL")

        # 5. Safety Standards (if explicitly represented in data)
        for sft in item.get("safety_standards", []):
            if isinstance(sft, dict):
                add_related(
                    sft.get("standard_number"),
                    sft.get("title"),
                    sft.get("relation", "GOVERNED_BY_SAFETY")
                )
            elif isinstance(sft, str):
                add_related(sft, None, "GOVERNED_BY_SAFETY")

        # 6. Quality Control Orders (QCO) Mandates (MANDATED_BY)
        qco_entries = item.get("compliance", [])
        if not qco_entries:
            qco_entries = self._get_qco_for_standard(standard_number)
        for qco in qco_entries:
            mandate = qco.get("mandate") or qco.get("mandated_by")
            if mandate:
                authority = qco.get("authority", "DPIIT / BIS")
                scheme = qco.get("scheme", "Mandatory QCO")
                add_related(mandate, f"{authority}: {scheme}", "MANDATED_BY")

        return related

    def _get_title_for_standard(self, standard_num: str) -> str:
        """Looks up cached standard title across registered nodes."""
        if not standard_num:
            return ""
        clean = standard_num.strip()
        target = self._memory_graph.get(clean)
        if not target:
            for k, v in self._memory_graph.items():
                if clean.lower() in k.lower() or k.lower() in clean.lower():
                    target = v
                    break
        return target.get("title", "") if target else ""

    def _get_qco_for_standard(self, standard_number: str) -> List[Dict[str, Any]]:
        """Loads and looks up verified QCO records for standard."""
        try:
            from pathlib import Path
            import json
            qco_path = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "qco_registry.json"
            if qco_path.exists():
                with open(qco_path, "r", encoding="utf-8") as f:
                    qco_reg = json.load(f)
                cleaned_std = standard_number.split(":")[0].strip()
                for key, entries in qco_reg.items():
                    if key in cleaned_std:
                        return entries
        except Exception as e:
            logger.debug(f"Could not check QCO registry: {e}")
        return []
