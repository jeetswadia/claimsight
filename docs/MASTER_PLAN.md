# Master Plan

12-week build plan for ClaimSight. Updated as I learn what works.

## What I'm building

A multi-agent system that takes a healthcare claim and runs it through specialist LLM agents to produce an adjudication recommendation with citations. Built on synthetic CMS data so there's no PHI risk.

The differentiator vs. most agentic AI demos: a real eval harness, citation provenance that's actually verified, and a fraud model alongside the LLM reasoning.

## Why this project

It hits the three role types I'm targeting (agentic AI, ML/DS, forward deployed) at the same time, and it's directly relevant to the insurance and healthcare companies on my interview list. Domain credibility from MetLife and Guardian carries over.

It's also defensibly hard. Anyone can wrap an LLM in a chat UI. A multi-agent system with calibrated fraud detection, hybrid retrieval, and a versioned eval harness is a different conversation.

## What it should prove by Week 12

Things a hiring manager can verify by clicking around the repo:

1. I can design and ship multi-agent systems beyond toy demos.
2. I understand evaluation rigor, not just model training.
3. I can blend classical ML with LLM reasoning.
4. I think about cost, latency, and production constraints.
5. I write clearly about technical work for non-technical stakeholders.
6. I have domain credibility in healthcare and insurance.

## Architecture

```
                    ┌─────────────────────┐
                    │   Claim arrives     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Intake Agent      │  parse, normalize, fetch member history
                    └──────────┬──────────┘
                               ▼
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
   ┌──────────────────┐ ┌────────────┐ ┌──────────────────┐
   │ Medical          │ │ Policy     │ │ Fraud Signal     │
   │ Necessity Agent  │ │ Compliance │ │ Agent            │
   │ (RAG)            │ │ Agent (RAG)│ │ (XGBoost + LLM)  │
   └────────┬─────────┘ └─────┬──────┘ └────────┬─────────┘
            └──────────────┬──┴─────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Prior Auth      │
                  │ Agent           │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │   Adjudicator   │  synthesize signals, produce recommendation
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │   Critic        │  can route back to specialists
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │  Final decision │  + citations + confidence + cost trace
                  └─────────────────┘
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Standard graph primitives, fast iteration. Refactor later if time |
| Cheap LLM | Groq Llama-3.3-70B | Free tier, fast, fine for specialists |
| Smart LLM | Claude Sonnet 4 | Adjudicator and critic only. Keeps cost bounded |
| Vector DB | pgvector on Supabase free tier | One database, one connection string |
| RDBMS | Postgres (Supabase) | Same instance |
| ML | XGBoost, scikit-learn | Fraud detection, calibration |
| Eval | Ragas + custom harness | Per-agent and end-to-end |
| Observability | Langfuse self-hosted | Free, full traces |
| Backend | FastAPI on Modal | Free tier, fast cold starts |
| Frontend | Next.js on Vercel | Free tier |
| Data | CMS SynPUF + synthesized policies/guidelines | No PHI, public, defensible |

## Data sources

All free, all public:

- **CMS SynPUF.** Synthetic Medicare claims, ~2.3M beneficiaries. The legitimate way to demo on healthcare data without touching PHI.
- **NPI Registry.** Provider directory, free download.
- **CMS Drug Pricing.** Open public data.
- **Clinical guidelines.** I'll synthesize realistic ones from public CMS coverage determination summaries (LCDs/NCDs are public).
- **Policy documents.** I'll write 10-15 realistic insurer policy excerpts. Clearly documented as synthetic.

## The eval harness

This is the differentiator. Most agent demos have no evals. Mine will have:

**Per-agent metrics**
- Retrieval: context precision, context recall, faithfulness (Ragas)
- Tool use: success rate, error recovery rate
- Citation accuracy: did the agent cite the right doc and the right span?

**End-to-end metrics**
- Agreement with ground truth (precision/recall on approve/deny/route)
- Hallucination rate (manual review of n=100 samples)
- Cost per claim (USD)
- P50/P95 latency
- Token efficiency

**Versioning story**
Each major change creates a new eval run. Dashboard shows metrics improving over time. This is what makes the project look like 3 months of real work.

## Deliverables

- [ ] Public GitHub repo, MIT license
- [ ] README with architecture diagram, demo, badges
- [ ] Live demo on Modal + Vercel
- [ ] 3-5 pre-loaded claim scenarios for the demo
- [ ] Long-form technical writeup on portfolio site
- [ ] Conference-talk-quality blog post
- [ ] 5-7 minute Loom walkthrough
- [ ] Eval results dashboard
- [ ] ADRs in docs/adr/

## Constraints I'm being honest about

- **Synthetic data only.** No PHI, ever. Lead with this in writeups.
- **Production-shaped, not production-ready.** Don't overclaim.
- **Fraud model is limited by synthetic data.** Frame as methodology demo, not a deployable asset.
- **Single-tenant.** Multi-tenancy is a real production concern not addressed here.

## Resume bullet draft

> **ClaimSight — Agentic Healthcare Claims Adjudication System** (independent, Feb 2026 - May 2026)
> Built a production-shaped multi-agent system for health insurance claims triage using LangGraph, pgvector, and a custom evaluation harness. Six specialist agents (medical necessity, policy compliance, fraud detection, prior auth, adjudication, critic) over CMS synthetic claims data. Integrated XGBoost fraud detection with LLM reasoning and citation-faithful RAG over clinical guidelines. Achieved [X]% agreement with ground-truth adjudications at $[Y] per claim, P95 latency [Z]s. Deployed on Modal/Vercel with full observability via Langfuse.

Fill in the metrics once they exist. Don't fake them.

## Public visibility plan

- **Week 2:** First LinkedIn post. "I'm building ClaimSight. Here's why."
- **Weeks 4, 6, 8, 10:** Build-in-public posts with technical detail.
- **Week 11:** Launch post + blog post on a Tuesday morning EST.
- **Week 12:** HN Show post + r/MachineLearning if quality warrants.
