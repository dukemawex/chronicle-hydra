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

## HydraDB

This project targets the open-source [HydraDB](https://github.com/hydra-db/hydradb) graph database and its OpenCypher query interface.
