# ADR-0002: Two-tier LLM strategy

Date: 2026-05-05
Status: Accepted

## Context

The system makes many LLM calls per claim. Every specialist agent calls a model, the adjudicator calls a model, the critic calls a model. If all calls go to a frontier model, cost per claim balloons fast and the project's free-tier constraint breaks. If all calls go to the cheapest model, quality on the hardest reasoning step (final adjudication) suffers.

The hardest reasoning is concentrated in two roles: the adjudicator (synthesizing conflicting signals into a defensible decision) and the critic (catching mistakes in the adjudicator's reasoning).

## Decision

Two tiers:

- **Tier 1, specialists.** Groq Llama-3.3-70B (free tier). Used by intake helpers, medical necessity, policy compliance, fraud reasoning, prior auth.
- **Tier 2, synthesizers.** Claude Sonnet 4 (paid). Used by the adjudicator and the critic only.

`src/agents/llm_router.py` abstracts this. Agents request `cheap` or `smart` and the router handles provider details. If keys are missing, the router falls back to a deterministic mock so the demo always runs.

## Alternatives considered

**Single tier (all Groq).** Cheaper, but adjudicator quality is materially worse in early experiments. It anchors on the most recent specialist output instead of weighing all signals.

**Single tier (all Claude).** Higher quality everywhere, but breaks the cost ceiling. Specialists do bounded retrieval-grounded reasoning that 70B-class models handle well.

**Three tiers (small / medium / large).** Marginal gain over two tiers, more complexity in the router.

## Consequences

**Enables**
- Stays under $0.10/claim target with current architecture
- Free tier viable for development and demo
- Demo runs end-to-end without any API keys (mock fallback)

**Costs**
- Two providers to manage (rate limits, errors, key rotation)
- The router becomes a piece of code that needs its own tests

**Reversible?** Yes, trivially. Change the router config.
