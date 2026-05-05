<div align="center">

# ClaimSight

**Production-shaped agentic claims adjudication for health insurance.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-orange)](https://github.com/astral-sh/ruff)
[![Status: Active development](https://img.shields.io/badge/status-active%20development-green)](docs/MASTER_PLAN.md)

[Architecture](#architecture) · [Quickstart](#quickstart) · [Roadmap](docs/MASTER_PLAN.md) · [Live demo](#live-demo) · [Writeup](#writeup)

</div>

---

## What is ClaimSight?

ClaimSight ingests a healthcare claim and runs it through a coordinated set of specialist LLM agents — medical necessity review, policy compliance, fraud detection, prior authorization — to produce an adjudication recommendation with full citations to the policy documents and clinical guidelines that justify the decision.

**Built on synthetic CMS data. No PHI, ever.**

This is a portfolio project, not a product. It is production-*shaped* — built the way a production system would be structured, with the eval rigor a real one would need — but not production-*ready*.

## Why this exists

Healthcare claims adjudication today is mostly humans reading PDFs and looking things up across three different systems. The tooling that does exist is either rule-based and brittle, or LLM-based and untrustworthy because it cannot cite its sources. ClaimSight is an attempt to show what an evaluation-driven agentic system for this problem could look like — and to demonstrate the engineering practices that would make such a system trustworthy.

## Architecture

<p align="center">
  <img src="docs/diagrams/architecture.svg" alt="ClaimSight architecture diagram" width="780">
</p>

For architectural decisions and tradeoffs, see [docs/adr/](docs/adr/).

## Tech stack

| Concern | Choice | Why |
|---|---|---|
| Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) | Standard, fast iteration |
| Cheap LLM | Groq Llama-3.3-70B | Free tier, fast specialists |
| Smart LLM | Claude Sonnet 4 | Adjudicator + critic only |
| Vector DB | pgvector on Supabase | One database, no extra service |
| Fraud model | XGBoost + SHAP | Calibrated, interpretable |
| Eval | [Ragas](https://github.com/explodinggradients/ragas) + custom harness | Per-agent and end-to-end |
| Observability | [Langfuse](https://langfuse.com/) | Full traces, free tier |
| Backend | FastAPI on [Modal](https://modal.com/) | Free tier, fast cold starts |
| Frontend | Next.js on Vercel | Free tier |

## Quickstart

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight

# Set up environment
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure secrets
cp .env.example .env
# Edit .env with your keys (see docs/SETUP.md)

# Verify everything is reachable
make verify

# Set up the database and load synthetic claims
make db-init
make data-load
```

Full setup walkthrough: [docs/SETUP.md](docs/SETUP.md).

## Repository layout

```
claimsight/
├── docs/                 # Architecture decisions, setup guide, weekly retros
│   ├── MASTER_PLAN.md    # Full 12-week roadmap
│   ├── WEEK_1_PLAN.md    # Day-by-day for week 1
│   ├── SETUP.md          # Detailed setup walkthrough
│   └── adr/              # Architecture Decision Records
├── scripts/              # Standalone scripts (data loading, env checks)
├── src/
│   ├── agents/           # Intake, specialists, adjudicator, critic
│   ├── data/             # Code lookups, member history, retriever
│   ├── db/               # Connection management
│   ├── evals/            # Eval harness, metrics, ground truth
│   ├── models/           # Pydantic schemas
│   └── api/              # FastAPI app
├── tests/
└── notebooks/            # Exploratory analysis
```

## Status

🚧 **Active development.** Week 1 of 12.

| Week | Focus | Status |
|---|---|---|
| 1 | Data foundation + intake | 🟢 In progress |
| 2 | First RAG agent (medical necessity) | ⚪ |
| 3 | Specialist agent suite | ⚪ |
| 4 | Fraud detection model | ⚪ |
| 5 | Adjudicator + critic loop | ⚪ |
| 6 | Eval harness v1 | ⚪ |
| 7 | Frontend | ⚪ |
| 8 | Deployment | ⚪ |
| 9-10 | Eval iteration + writeup | ⚪ |
| 11 | Polish + launch | ⚪ |
| 12 | Iterate on feedback | ⚪ |

## Live demo

🔗 *Coming end of Week 8.*

## Writeup

📖 *Coming end of Week 11. Topic: Building Production Agentic Systems for Healthcare — Evals, Failure Modes, and the Honest Tradeoffs.*

## Eval results

| Metric | Baseline | Current |
|---|---|---|
| Adjudication agreement (vs. ground truth) | TBD | TBD |
| Citation faithfulness | TBD | TBD |
| Hallucination rate (sampled, n=100) | TBD | TBD |
| Cost per claim (USD) | TBD | TBD |
| P50 / P95 latency (s) | TBD | TBD |

Real numbers, populated as the system improves.

## Contributing

This is primarily a portfolio project, but issues and discussions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Author

**Jeet S Swadia** — ML/AI Engineer, Boston, MA
[LinkedIn](https://linkedin.com/in/jeetsswadia) · [Portfolio](https://jeetsswadia.com) · [AIM Academy](https://aimacademy.us)
