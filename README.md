# Chronicle — temporal, abstaining agent memory

Chronicle is a Hack Hydra Track 3 submission. It stores session messages and extracted assertions in HydraDB, preserves revisions and validity intervals, and answers with evidence paths or an explicit abstention when the history does not support an answer.

## Why HydraDB

Vector search can retrieve similar messages, but it does not make temporal revision, contradiction, or evidence-path queries first-class. Chronicle uses HydraDB as the source of truth for a graph of sessions, entities, assertions, revisions, and supporting messages. The answer layer runs bounded OpenCypher traversals before asking the model to phrase a response.

## Status

Day 1 scaffold. All participant-authored work starts on or after 2026-08-12, as required by Hack Hydra.

## Planned demo

1. A preference is stated in Session 1.
2. The user revises it in Session 3.
3. Chronicle answers the current preference and the historical preference separately.
4. An unrelated question returns `NOT_IN_MEMORY` with no invented answer.

## Built on the HydraDB open-source repo

This repository pins the HydraDB OS source as `vendor/hydradb` via a Git submodule. The hosted API is the default demo runtime; the pinned source is the local/self-hosted runtime and the reference for the graph model and OpenCypher behavior.

```bash
git clone --recurse-submodules <this-repository-url>
# or, after cloning:
git submodule update --init --recursive
```

## HydraDB

This project targets the open-source [HydraDB](https://github.com/hydra-db/hydradb) graph database and its OpenCypher query interface.

## What Chronicle loses without HydraDB

Chronicle is not a README integration. The live answer path calls HydraDB's `context/ingest` with structured session records, then calls HydraDB `/query` with `graph_context=true`. HydraDB extracts and returns the entity/relation paths used to answer. Without HydraDB, Chronicle loses the durable cross-session graph, revision links, provenance paths, temporal retrieval, and its ability to distinguish “superseded” from “current” instead of concatenating similar chunks.

## Run the demo

```bash
pip install -e .
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The UI calls the FastAPI graph-backed routes; the HydraDB key stays server-side.
