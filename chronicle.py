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
HYDRA_GRAPH = os.getenv("HYDRA_GRAPH", "default-tenant")
HYDRA_COLLECTION = os.getenv("HYDRA_COLLECTION", "chronicle")
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
    collection: str = HYDRA_COLLECTION

    @property
    def hosted(self) -> bool:
        return self.base_url.startswith("https://")

    async def ingest_app_knowledge(self, items: list[dict]) -> dict:
        if not self.hosted:
            raise RuntimeError("app_knowledge ingestion requires hosted HydraDB v2")
        import json
        files = {"app_knowledge": (None, json.dumps(items))}
        data = {"type": "knowledge", "database": self.graph, "collection": self.collection, "upsert": "true"}
        headers = {"Authorization": f"Bearer {self.token}", "API-Version": "2"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url.rstrip('/')}/context/ingest", headers=headers, data=data, files=files)
            response.raise_for_status()
            return response.json()

    async def ingest_session(self, session_id: str, messages: list[dict]) -> dict:
        items = [{"id": f"{session_id}-{i}", "database": self.graph, "collection": self.collection,
                  "title": f"Session {session_id}", "type": "conversation",
                  "content": {"text": f"{m.get('role','user')}: {m.get('text','')}"},
                  "metadata": {"session_id": session_id, "at": m.get("at")},
                  "additional_metadata": {"source": "chronicle"}}
                 for i, m in enumerate(messages)]
        return await self.ingest_app_knowledge(items)

    async def ingest_text(self, text: str, title: str = "chronicle-demo") -> dict:
        if not self.hosted:
            return await self.query(text)
        import json
        files = {"memories": (None, json.dumps([{"text": text, "infer": False, "title": title}]))}
        data = {"type": "memory", "database": self.graph, "collection": self.collection, "upsert": "true"}
        headers = {"Authorization": f"Bearer {self.token}", "API-Version": "2"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url.rstrip('/')}/context/ingest", headers=headers, data=data, files=files)
            response.raise_for_status()
            return response.json()

    async def query(self, cypher: str) -> dict:
        url = f"{self.base_url.rstrip('/')}/query" if self.base_url.startswith("https://") else f"{self.base_url.rstrip('/')}/v1/graphs/{self.graph}/query"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"database": self.graph, "collection": self.collection, "query": cypher, "type": "all", "mode": "thinking", "graph_context": True} if self.base_url.startswith("https://") else {"cell_id": self.cell, "query": cypher}
        if self.base_url.startswith("https://"):
            headers["API-Version"] = "2"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def setup_demo(self) -> None:
        if self.hosted:
            await self.ingest_text("""Session 1: Emmanuel prefers vim.
Session 2: Emmanuel revises the preference and prefers neovim from now on.
Historical value: vim. Current value: neovim.
Evidence: session-1 and session-2.""", "chronicle-temporal-demo")
            return
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
        if self.hosted:
            return await self.query(
                f"What is the current value of {predicate} for {subject}? "
                "Distinguish the current assertion from superseded assertions and include evidence paths."
            )
        return await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}, state:'current'}})
        OPTIONAL MATCH (a)-[:SUPPORTED_BY]->(m:Message)
        RETURN a.value AS value, a.valid_from AS valid_from, collect(m.id) AS evidence
        LIMIT 1
        """)

    async def history(self, subject: str, predicate: str) -> dict:
        if self.hosted:
            return await self.query(
                f"Show the chronological history of {predicate} for {subject}. "
                "Include revisions, superseded values, validity times, and supporting messages."
            )
        return await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}}})
        OPTIONAL MATCH (a)-[:SUPPORTED_BY]->(m:Message)
        RETURN a.value AS value, a.state AS state, a.valid_from AS valid_from, a.valid_to AS valid_to, collect(m.id) AS evidence
        ORDER BY a.valid_from
        """)

    async def abstain(self, subject: str, predicate: str) -> dict:
        if self.hosted:
            result = await self.query(
                f"Is there any recorded assertion for {predicate} about {subject}? "
                "Return no result rather than inventing one if the memory graph has no evidence."
            )
            if not (result.get("data") or {}).get("chunks"):
                return {"status": "NOT_IN_MEMORY", "evidence": []}
            return result
        result = await self.query(f"""
        MATCH (a:Assertion {{subject:{_q(subject)}, predicate:{_q(predicate)}}})
        RETURN count(a) AS matches
        """)
        return {"status": "NOT_IN_MEMORY"} if not result.get("data") else result
