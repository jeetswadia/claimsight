# Architecture Decision Records

ADRs capture significant architectural decisions: what we chose, what we considered, and why we chose what we chose. They are append-only — when a decision changes, write a new ADR that supersedes the old one.

## Index

- [ADR-0001: Use LangGraph for orchestration](0001-use-langgraph-for-orchestration.md)
- [ADR-0002: Two-tier LLM strategy](0002-two-tier-llm-strategy.md)
- [ADR-0003: Postgres + pgvector as single data store](0003-postgres-pgvector-single-store.md)
- [ADR-0004: Synthetic data only](0004-synthetic-data-only.md)

## Format

Each ADR follows this template:

```
# ADR-NNNN: Short title

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded by ADR-NNNN

## Context

What problem are we solving? What constraints are in play?

## Decision

What did we decide?

## Alternatives considered

What else did we evaluate? Why didn't we pick those?

## Consequences

What does this enable? What does this make harder? What do we lose?
```
