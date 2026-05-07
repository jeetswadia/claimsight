# ClaimSight

Multi-agent system for healthcare claims adjudication. Reads a claim, runs it through specialist LLM agents (medical necessity, policy compliance, fraud, prior auth), and returns a decision with citations back to the specific guideline text that justified it.

Built on synthetic CMS data. No PHI.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-orange)](https://github.com/astral-sh/ruff)

[Demo](#run-the-demo) · [Architecture](#architecture) · [Roadmap](docs/MASTER_PLAN.md) · [ADRs](docs/adr/) · [Setup](docs/SETUP.md)

## Run the demo

No API keys, no database, no SynPUF download. The demo ships with three synthetic claims and a deterministic mock LLM so you can see the pipeline run before plugging in real models.

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight
pip install -e .
python scripts/demo.py
```

Drop a `GROQ_API_KEY` in a `.env` file ([free tier here](https://console.groq.com/)) and the same command runs against a real LLM. Same code path, different model.

### Sample output

```
────────────────────── ClaimSight Demo — knee-mri ──────────────────────
MRI of knee for chronic pain after conservative treatment failure

╭───────────── Claim Packet ─────────────╮
│  Procedure         73721 — MRI knee    │
│  Primary diagnosis M17.11 — OA, right  │
│  Billed amount     $1,450.00           │
│  History (recent)  • Office visit      │
│                    • Physical therapy  │
│                    • Office visit      │
╰────────────────────────────────────────╯

╭──── Medical Necessity Agent  (✓ APPROVE) ────╮
│  Decision     ✓ APPROVE                       │
│  Confidence   88%                             │
│  Rationale    Patient has documented OA with  │
│               prior physical therapy and      │
│               office visits over 6+ weeks,    │
│               consistent with conservative    │
│               therapy failure...              │
│  Citations    2 chunk(s) cited                │
│  chunk 101    "conservative management ...    │
│               at least 6 weeks has failed"    │
│  chunk 102    "advanced imaging is generally  │
│               reserved for cases where..."    │
╰───────────────────────────────────────────────╯
```

### Three scenarios

```bash
python scripts/demo.py --list                # show all scenarios
python scripts/demo.py --claim knee-mri      # routine approval
python scripts/demo.py --claim cosmetic      # clear denial (Z41.1 exclusion)
python scripts/demo.py --claim ambiguous     # routes to human review
```

Each one is hand-crafted to hit a different decision path. Citations link back to specific chunks of the underlying policy text, so every decision has receipts.

## What it does

A claim comes in. It goes through:

1. **Intake** parses the claim, normalizes codes, pulls member history. Pure deterministic Python, no LLM.
2. **Medical Necessity** runs RAG over clinical guidelines and checks if the procedure fits the diagnosis.
3. **Policy Compliance** runs RAG over insurer policies and checks coverage rules.
4. **Fraud Signal** runs an XGBoost model on engineered features, then has an LLM reason over the score.
5. **Prior Auth** checks whether PA was required and whether it was obtained.
6. **Adjudicator** synthesizes the specialist outputs into a decision with confidence and citations.
7. **Critic** does a second pass and can route work back to specialists if the adjudicator's reasoning has gaps.

Each agent returns a structured finding with a decision signal, confidence, rationale, and citations. The adjudicator weighs them. Nothing is allowed to make a claim without a citation back to source text.

## Why this exists

Claims adjudication is mostly humans reading PDFs and looking things up across three different systems. The tooling that exists is either rule-based and brittle, or LLM-based and untrustworthy because it can't show its work.

This is what an evaluation-driven agentic version could look like. Portfolio project, not a product. Production-shaped, not production-ready. The difference matters.

## What you can verify by reading the code

| Thing | Where |
|---|---|
| Multi-agent design | [`src/agents/`](src/agents/), [ADR-0001](docs/adr/0001-use-langgraph-for-orchestration.md) |
| Citation provenance (matching LLM citations back to retrieved chunks) | [`src/agents/medical_necessity.py`](src/agents/medical_necessity.py) — see the `review()` function |
| Two-tier LLM routing for cost control | [`src/agents/llm_router.py`](src/agents/llm_router.py), [ADR-0002](docs/adr/0002-two-tier-llm-strategy.md) |
| One database for relational + vector + traces | [`scripts/02_apply_schema.sql`](scripts/02_apply_schema.sql), [ADR-0003](docs/adr/0003-postgres-pgvector-single-store.md) |
| Synthetic-only data boundary | [ADR-0004](docs/adr/0004-synthetic-data-only.md) |
| Engineering hygiene (CI, ADRs, conventional commits) | [`.github/workflows/ci.yml`](.github/workflows/ci.yml), [`docs/adr/`](docs/adr/), commit history |
| Graceful degradation | LLM router falls back to mock when keys are missing. SynPUF script falls back to Synthea. |

## Architecture

<p align="center">
  <img src="docs/diagrams/architecture.svg" alt="ClaimSight architecture diagram" width="780">
</p>

The four ADRs in [docs/adr/](docs/adr/) cover the orchestration choice, the two-tier LLM strategy, the single-database decision, and why everything stays synthetic.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) | Standard graph primitives, fast to iterate |
| Cheap LLM | Groq Llama-3.3-70B | Free tier, fast, fine for specialists |
| Smart LLM | Claude Sonnet 4 | Adjudicator and critic only, where reasoning matters |
| Vector + relational DB | pgvector on Supabase | One database, one connection string |
| Fraud model | XGBoost + SHAP | Calibrated, interpretable, easy to integrate |
| Eval | [Ragas](https://github.com/explodinggradients/ragas) + custom harness | Per-agent and end-to-end metrics |
| Observability | [Langfuse](https://langfuse.com/) | Full traces, free tier |
| Backend | FastAPI on [Modal](https://modal.com/) | Free tier, fast cold starts |
| Frontend | Next.js on Vercel | Free tier |

## What works right now

| Component | Status |
|---|---|
| Pydantic schemas for the full pipeline | ✅ |
| Postgres + pgvector schema | ✅ |
| Code lookups (CPT, ICD-10, NPI) | ✅ |
| Member history retrieval | ✅ |
| Intake agent | ✅ |
| LLM router with mock fallback | ✅ |
| Medical necessity agent (real LLM, real citations) | ✅ |
| Demo script with three scenarios | ✅ |
| Policy compliance agent | Week 2 |
| Fraud signal agent (XGBoost + LLM) | Week 4 |
| Adjudicator + critic | Week 5 |
| Eval harness | Week 6 |
| Web UI | Week 7 |
| Live deployment | Week 8 |

## Layout

```
claimsight/
├── docs/
│   ├── MASTER_PLAN.md    # 12-week roadmap
│   ├── WEEK_1_PLAN.md    # day-by-day for week 1
│   ├── SETUP.md          # full setup walkthrough
│   ├── adr/              # architecture decision records
│   └── diagrams/         # SVG architecture diagrams
├── scripts/
│   ├── demo.py           # end-to-end demo, no setup needed
│   ├── 00_verify_env.py  # env health check
│   ├── 01_download_synpuf.py
│   └── 02_apply_schema.sql
├── src/
│   ├── agents/           # intake, medical_necessity, llm_router
│   ├── data/             # code lookups, member history
│   ├── db/               # connection
│   ├── models/           # pydantic schemas
│   ├── evals/            # week 6
│   └── api/              # week 7
├── tests/
└── notebooks/
```

## Setup

For the demo, the three commands above are everything.

For the full dev environment (database, real LLM keys, all agents) see [docs/SETUP.md](docs/SETUP.md).

## Roadmap

| Week | Focus | Status |
|---|---|---|
| 1 | Data foundation, intake, first LLM agent | In progress |
| 2 | Specialist agents (policy, prior auth) | |
| 3 | Real retrieval pipeline + corpus | |
| 4 | Fraud detection model | |
| 5 | Adjudicator + critic loop | |
| 6 | Eval harness v1 | |
| 7 | Frontend | |
| 8 | Deployment | |
| 9-10 | Eval iteration + writeup | |
| 11 | Polish + launch | |
| 12 | Iterate on feedback | |

## Eval results

| Metric | Baseline | Current |
|---|---|---|
| Adjudication agreement vs ground truth | TBD | TBD |
| Citation faithfulness | TBD | TBD |
| Hallucination rate (sampled, n=100) | TBD | TBD |
| Cost per claim (USD) | TBD | TBD |
| P50 / P95 latency (s) | TBD | TBD |

Real numbers go here as the system gets better. Nothing made up.

## Live demo

Coming end of Week 8. The CLI demo is the current proof of life.

## Writeup

Coming end of Week 11. Working title: building production agentic systems for healthcare, evals, failure modes, honest tradeoffs.

## Contributing

Issues and discussions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## Author

Jeet S Swadia. ML/AI Engineer, Boston.
[LinkedIn](https://linkedin.com/in/jeetsswadia) · [Portfolio](https://jeetsswadia.com) · [AIM Academy](https://aimacademy.us)
