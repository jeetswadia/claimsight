# ADR-0001: Use LangGraph for orchestration

Date: 2026-05-05
Status: Accepted

## Context

ClaimSight needs to orchestrate multiple LLM agents (intake, medical necessity, policy compliance, fraud, prior auth, adjudicator, critic) with conditional routing. The critic, for example, can send work back to specialists for a second pass.

What I need from the orchestration layer:

- Explicit state management across agent calls
- Conditional edges based on agent output
- Streaming and observability hooks
- Reasonable defaults so I ship in 12 weeks, not 24

## Decision

Use LangGraph for the agent graph. Build a thin abstraction layer (`src/agents/graph.py`) so individual agents stay framework-agnostic where possible. Agents accept and return our own pydantic models, not LangChain types.

## Alternatives considered

**Roll my own orchestration.** More impressive on a portfolio, but adds 2-3 weeks building primitives that already exist. Saved as a possible refactor in Week 11 if there's time.

**CrewAI.** Higher-level, more opinionated. The opinions don't quite match this domain. CrewAI assumes role-playing agents. I need stricter, citation-bound specialists. Less observable internally too.

**AutoGen.** Heavier, more focused on multi-turn conversation patterns than directed graphs. Graph model fits better.

**Plain function calls + a state dict.** Tempting for simplicity, but the conditional routing (critic → specialists) makes this awkward fast.

## Consequences

**Enables**
- Fast first cut of the agent graph
- Built-in checkpointing for resumable runs
- Easy integration with LangSmith / Langfuse traces

**Costs**
- LangChain ecosystem churn risk. Pin versions tightly.
- Some idiomatic LangGraph patterns leak into our code. Mitigated by the abstraction layer.

**Reversible?** Yes. Agents themselves are framework-agnostic. Swapping orchestrators in Week 11 is a 1-2 day refactor, not a rewrite.
