# ADR-0001: Use LangGraph for orchestration

Date: 2026-05-05
Status: Accepted

## Context

ClaimSight needs to orchestrate multiple LLM agents (intake, medical necessity, policy compliance, fraud, prior auth, adjudicator, critic) with conditional routing — the critic, for example, can send work back to specialists for a second pass. We need:

- Explicit state management across agent calls
- Conditional edges based on agent output
- Streaming and observability hooks
- Reasonable defaults so we ship in 12 weeks, not 24

## Decision

Use LangGraph for the agent graph. Build a thin abstraction layer (`src/agents/graph.py`) so individual agents are framework-agnostic where possible — they accept and return our own pydantic models, not LangChain types.

## Alternatives considered

**Roll our own orchestration.** More impressive on a portfolio, but adds 2-3 weeks of work building primitives that already exist. Saved as a possible refactor in Week 11 if time permits.

**CrewAI.** Higher-level, more opinionated. The opinions don't quite match this domain (CrewAI assumes role-playing agents; we need stricter, citation-bound specialists). Less observable internally.

**AutoGen.** Heavier, more focused on multi-turn conversation patterns than directed graphs. The graph model fits our problem better.

**Plain function calls + a state dict.** Tempting for simplicity, but the conditional routing (critic → specialists) makes this awkward fast.

## Consequences

**Enables:**
- Fast first cut of the agent graph
- Built-in checkpointing for resumable runs
- Easy integration with LangSmith / Langfuse traces

**Costs:**
- LangChain ecosystem churn risk; pin versions tightly
- Some idiomatic LangGraph patterns leak into our code; mitigated by the abstraction layer

**Reversible?** Yes. The agents themselves are framework-agnostic. Swapping orchestrators in Week 11 is a 1-2 day refactor, not a rewrite.
