# ClaimSight — Master Plan

**Project:** Agentic claims triage and adjudication assistant for health insurance.
**Timeline:** 12 weeks, full-time.
**Author:** Jeet S Swadia
**Status:** Active build

---

## The 30-second pitch

ClaimSight ingests a healthcare claim, runs it through a coordinated set of specialist agents (medical necessity, policy compliance, fraud signals, prior authorization), and produces an adjudication recommendation with full citations to the policy documents and clinical guidelines that justify the decision. Built on synthetic CMS data with a production-shaped architecture and a real evaluation harness.

## What this project proves

Each capability below is something a hiring manager can verify by clicking around the repo:

1. You can design and ship multi-agent systems beyond toy demos.
2. You understand evaluation rigor, not just model training.
3. You can blend classical ML (fraud detection) with LLM reasoning.
4. You think about cost, latency, and production constraints.
5. You write clearly about technical work for non-technical stakeholders.
6. You have domain credibility in healthcare and insurance.

## Architecture at a glance

```
                    ┌─────────────────────┐
                    │   Claim arrives     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Intake Agent      │  parses, normalizes, fetches member history
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
                  │   Adjudicator   │  synthesizes signals, produces recommendation
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

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Standard, fast to start, refactor later if time permits |
| LLM (cheap) | Groq Llama-3.3-70B | Free tier, fast, good enough for specialists |
| LLM (smart) | Claude Sonnet 4 | Adjudicator and critic only; keeps cost bounded |
| Vector DB | pgvector on Supabase free tier | One database, no extra service |
| RDBMS | Postgres (Supabase) | Same instance |
| ML | XGBoost, scikit-learn | Fraud detection, calibration |
| Eval | Ragas + custom harness | Per-agent and end-to-end |
| Observability | Langfuse self-hosted | Free, full traces |
| Backend | FastAPI on Modal | Free tier, fast cold starts |
| Frontend | Next.js on Vercel | Free tier, ships easy |
| Data | CMS SynPUF + synthesized policies/guidelines | No PHI, public, defensible |

## Data sources (all free, all public)

- **CMS SynPUF** — synthetic Medicare claims, ~2.3M beneficiaries. The legitimate way to demo on healthcare data without touching PHI.
- **NPI Registry** — provider directory, free download.
- **CMS Drug Pricing** — open public data.
- **Clinical guidelines** — synthesize realistic ones from public CMS coverage determination summaries (LCDs/NCDs are public).
- **Policy documents** — write 10-15 realistic insurer policy excerpts. This is fair game and clearly documented as synthetic.

## The eval harness (this is the differentiator)

Most agent demos have no evals. Yours will have:

**Per-agent metrics**
- Retrieval: context precision, context recall, faithfulness (Ragas)
- Tool use: success rate, error recovery rate
- Citation accuracy: did the agent cite the right doc and the right span?

**End-to-end metrics**
- Agreement with ground truth (precision/recall on approve/deny/route)
- Hallucination rate (manual review of N=100 samples)
- Cost per claim (USD)
- P50/P95 latency
- Token efficiency (output tokens per useful claim word)

**Versioning story**
- Each major change creates a new eval run.
- Dashboard shows metrics improving over time.
- This is what makes the project look like 3 months of real work.

## Deliverables checklist

- [ ] GitHub repo, public, MIT license
- [ ] README with architecture diagram, demo GIF, badges
- [ ] Live demo on Modal + Vercel
- [ ] 3-5 pre-loaded claim scenarios for the demo
- [ ] Long-form technical writeup on portfolio site
- [ ] Conference-talk-quality blog post
- [ ] 5-7 minute Loom walkthrough
- [ ] Eval results dashboard
- [ ] Architecture decision records (ADRs) in /docs

## Honest constraints (talk about these openly)

- Synthetic data only. No PHI, ever. Lead with this.
- Production-shaped, not production-ready. Don't overclaim.
- Fraud model limited by synthetic data quality. Frame as methodology demo.
- Single-tenant; multi-tenancy is a real production concern not addressed here.

## Resume bullet (draft)

> **ClaimSight — Agentic Healthcare Claims Adjudication System** (independent, Feb 2026–May 2026)
> Built a production-shaped multi-agent system for health insurance claims triage using LangGraph, pgvector, and a custom evaluation harness. Coordinated 6 specialist agents (medical necessity, policy compliance, fraud detection, prior auth, adjudication, critic) over CMS synthetic claims data. Integrated XGBoost fraud detection with LLM reasoning and citation-faithful RAG over clinical guidelines. Achieved [X]% agreement with ground-truth adjudications at $[Y] per claim, P95 latency [Z]s. Deployed on Modal/Vercel with full observability via Langfuse.

(Fill in metrics once you have them. Don't fake them.)

## Public visibility plan

- **Week 2:** First LinkedIn post — "I'm building ClaimSight. Here's why."
- **Weeks 4, 6, 8, 10:** Build-in-public posts with technical detail.
- **Week 11:** Launch post + blog post on a Tuesday morning EST.
- **Week 12:** HN Show post + r/MachineLearning if quality warrants.

## What "done" means

A recruiter visits your portfolio, watches the 90-second demo video, clicks the live demo, runs a sample claim, sees the agent trace, reads the writeup, and thinks: *"This person has done senior agentic AI work. I want to talk to them."*

That is the only success metric that matters.
