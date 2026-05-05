# ADR-0003: Postgres + pgvector as single data store

Date: 2026-05-05
Status: Accepted

## Context

ClaimSight needs three storage capabilities:

1. Relational data (claims, members, providers, codes)
2. Vector search over knowledge documents (policies, guidelines)
3. Trace storage for agent runs (structured JSON)

We could use three different services, but every additional managed service is one more thing to provision, monitor, and pay for. The free-tier constraint pushes us toward consolidation.

## Decision

Single Postgres database with the `pgvector` extension. Hosted on Supabase free tier in development; portable to any Postgres in production.

- Relational tables for claims/members/providers/codes
- `vector(1024)` columns for embeddings, with HNSW indexes
- `tsvector` for BM25-style full-text search (hybrid retrieval)
- `JSONB` for agent step traces

## Alternatives considered

**Postgres + Pinecone.** Cleaner separation, but Pinecone free tier is restrictive and adds an external service. pgvector performs well for our scale (thousands of chunks, not millions).

**Postgres + Weaviate.** More features (multi-tenancy, hybrid search built-in), but heavier to operate and overkill for the demo scale.

**SQLite + FAISS.** Local-only, no managed option, awkward to deploy.

**MongoDB.** Loses relational integrity guarantees that matter for claims data.

## Consequences

**Enables:**
- One connection string, one set of credentials
- Atomic transactions across structured and vector data
- Native joins between agent traces and the claims they processed
- Free-tier viable

**Costs:**
- pgvector HNSW performance degrades at very high scale (10M+ vectors); not a concern at portfolio scale
- Supabase free-tier has a database size cap; we'll monitor

**Reversible?** Mostly. Migrating to a dedicated vector DB later is straightforward; the retriever interface (`src/data/retriever.py`) abstracts the storage choice.
