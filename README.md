# ClaimSight

> Production-shaped agentic claims adjudication for health insurance.

ClaimSight ingests a healthcare claim and runs it through a coordinated set of specialist LLM agents — medical necessity review, policy compliance, fraud detection, prior authorization — to produce an adjudication recommendation with full citations to the policy documents and clinical guidelines that justify the decision.

Built on synthetic CMS data. No PHI, ever.

## Why this exists

Most healthcare claims are still triaged by humans reading PDFs and looking things up in three different systems. The tooling that does exist is either rule-based and brittle or LLM-based and untrustworthy. ClaimSight is an attempt to show what an evaluation-driven agentic system for this problem could actually look like.

This is a portfolio project, not a product. It is production-*shaped*, not production-*ready*.

## What it does

Given a claim:

1. **Intake** — parses the claim, normalizes codes, retrieves member history.
2. **Medical Necessity** — RAG over clinical guidelines; checks alignment with diagnosis.
3. **Policy Compliance** — RAG over insurer policies; checks coverage.
4. **Fraud Signal** — XGBoost model + LLM reasoning over the score.
5. **Prior Auth** — verifies if PA was required and obtained.
6. **Adjudicator** — synthesizes signals, produces recommendation with confidence.
7. **Critic** — second-pass review, can route back for more analysis.

Every decision comes with citations. Every run is traced. Every metric is measured.

## Stack

LangGraph · Postgres + pgvector · XGBoost · FastAPI · Modal · Next.js · Vercel · Langfuse · Ragas

## Status

🚧 In active development. See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for the full roadmap.

## Getting started

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in your keys
python scripts/00_verify_env.py
```

See [docs/SETUP.md](docs/SETUP.md) for the full setup guide.

## Demo

🔗 Live demo: [coming soon]
🎥 Walkthrough: [coming soon]
📖 Technical writeup: [coming soon]

## Eval results

| Metric | Baseline | Current |
|---|---|---|
| Adjudication agreement | TBD | TBD |
| Citation faithfulness | TBD | TBD |
| Hallucination rate | TBD | TBD |
| Cost per claim | TBD | TBD |
| P95 latency | TBD | TBD |

## License

MIT

## Author

Jeet S Swadia — [LinkedIn](https://linkedin.com/in/jeetsswadia) · [Portfolio](https://jeetsswadia.com)
