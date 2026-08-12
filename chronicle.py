"""Chronicle's small, explicit HydraDB graph layer.

HydraDB is accessed over its OpenCypher-compatible HTTP endpoint. The graph
schema is the product: temporal assertions and their provenance are not hidden
inside a vector index.
"""
from __future__ import annotations
import os, re
from dataclasses import dataclass
from typing import Any
import httpx

HYDRA_URL = os.getenv("HYDRA_URL", "http://127.0.0.1:8443")
HYDRA_TOKEN = os.getenv("HYDRA_TOKEN", "local-development-token-32-bytes")
HYDRA_GRAPH = os.getenv("HYDRA_GRAPH", "default")
HYDRA_CELL = os.getenv("HYDRA_CELL", "cell-0")


def _q(value: Any) -> str:
    """Cypher string literal for demo-safe values."""
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ") + "'"


@dataclass
class HydraClient:
    base_url: str = HYDRA_URL
    token: str = HYDRA_TOKEN
    graph: str = HYDRA_GRAPH
    cell: str = HYDRA_CELL

    async def query(self, cypher: str) -> dict:
        url = f"{self.base_url.rstrip('/')}/v1/graphs/{self.graph}/query"
        headers = {"Authorization": f"Bearer {self.token}", "X-Graph-Namespace": "default"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json={"cell_id": self.cell, "query": cypher})
            response.raise_for_status()
            return response.json()

    async def setup_demo(self) -> None:
        await self.query("""
        CREATE
          (s1:Session {id:'s1', started_at:'2026-08-12T10:00:00Z'}),
          (s2:Session {id:'s2', started_at:'2026-08-12T11:00:00Z'}),
          (s3:Session {id:'s3', started_at:'2026-08-12T12:00:00Z'}),
          (u:Entity {id:'emmanuel', name:'Emmanuel'}),
          (a1:Assertion {id:'a1', subject:'Emmanuel', predicate:'preferred_editor', value:'vim', valid_from:'2026-08-12T10:05:00Z', valid_to:'2026-08-12T11:30:00Z', state:'superseded'}),
          (a2:Assertion {id:'a2', subject:'Emmanuel', predicate:'preferred_editor', value:'neovim', valid_from:'2026-08-12T11:30:00Z', state:'current'}),
          (m1:Message {id:'m1', text:'I prefer vim.', at:'2026-08-12T10:05:00Z'}),
          (m2:Message {id:'m2', text:'Actually, use neovim from now on.', at:'2026-08-12T11:30:00Z'}),
          (s1)-[:CONTAINS]->(m1), (s2)-[:CONTAINS]->(m2),
          (u)-[:ASSERTED {at:'2026-08-12T10:05:00Z'}]->(a1),
          (u)-[:ASSERTED {at:'2026-08-12T11:30:00Z'}]->(a2),
          (a2)-[:REVISES]->(a1),
          (a1)-[:SUPPORTED_BY]->(m1), (a2)-[:SUPPORTED_BY]->(m2)
        """)

    async def current_assertion(self, subject: str, predicate: str) -> dict:
        return await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}, state:'current'}})
        OPTIONAL MATCH (a)-[:SUPPORTED_BY]->(m:Message)
        RETURN a.value AS value, a.valid_from AS valid_from, collect(m.id) AS evidence
        LIMIT 1
        """)

    async def history(self, subject: str, predicate: str) -> dict:
        return await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}}})
        OPTIONAL MATCH (a)-[:SUPPORTED_BY]->(m:Message)
        RETURN a.value AS value, a.state AS state, a.valid_from AS valid_from, a.valid_to AS valid_to, collect(m.id) AS evidence
        ORDER BY a.valid_from
        """)

    async def abstain(self, subject: str, predicate: str) -> dict:
        result = await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}}})
        RETURN count(a) AS matches
        """)
        # The app layer treats zero matches as a first-class answer.
        return {"status": "NOT_IN_MEMORY"} if not result.get("data") else result
