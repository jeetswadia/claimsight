# Week 1 — Foundations

**Goal by Friday:** working data pipeline that loads SynPUF claims into Postgres, plus code mappings, member history queries, and a basic intake agent that parses a claim and pulls the relevant context. No LLM agent loop yet. Just the substrate.

**Why this week looks boring:** every weak agentic AI project skips this and tries to do agent stuff first. The data layer is what makes the rest possible. This is the foundation that lets weeks 3-8 actually work.

## Monday — environment + repo

**Morning (3-4 hrs)**
- Push the scaffolded repo to GitHub. Public. MIT license.
- Set up Python 3.11 venv, install dependencies (pyproject.toml provided).
- Set up pre-commit hooks (ruff, black, mypy).
- Create Supabase project (free tier). Save connection string in `.env`.
- Verify pgvector extension is enabled.

**Afternoon (3-4 hrs)**
- Sign up for: Modal, Vercel, Groq (free tier), Langfuse Cloud or self-host.
- Get API keys. Store in `.env`. Document in README setup section.
- Run `scripts/00_verify_env.py`. It pings every service.
- First commit, first push. Repo is live.

**End of day:** repo exists, services connected, the verify script passes.

## Tuesday — SynPUF + schema

**Morning (4 hrs)**
- Run `scripts/01_download_synpuf.py`. Pulls a SynPUF sample.
- SynPUF is large. Only pull Sample 1 (~10K beneficiaries) which is plenty.
- Inspect the raw files. Document the schema in `docs/data_dictionary.md`.

**Afternoon (4 hrs)**
- Apply the database schema (`scripts/02_apply_schema.sql`).
- Run `scripts/03_load_synpuf.py` to load beneficiaries, claims, providers.
- Spot-check with SQL: are claim counts reasonable, are joins working?

**End of day:** Postgres has real (synthetic) claims data. Can query "show me all claims for member X."

## Wednesday — code mappings + provider data

**Morning (4 hrs)**
- Load CPT/ICD-10 reference data. Use the public CMS code sets.
- Load NPI provider directory subset. A few thousand providers is plenty for demo.
- Build `src/data/code_lookup.py`. Utilities to translate codes to descriptions.

**Afternoon (4 hrs)**
- Synthesize 15 realistic policy documents covering common scenarios (preventive care, imaging, surgery, mental health, drugs, etc.). Use Claude or GPT to draft them, then edit for realism.
- Synthesize 20 clinical guideline summaries. Same approach.
- These go in `data/synthetic/policies/` and `data/synthetic/guidelines/` as markdown.

**End of day:** can look up any code, find any provider, and have a corpus of policies and guidelines to embed tomorrow.

## Thursday — embeddings + retrieval

**Morning (4 hrs)**
- Set up the embeddings pipeline. Use `BAAI/bge-large-en-v1.5` via sentence-transformers (free, runs locally) or Voyage AI free tier.
- Chunk policies and guidelines (semantic chunking, 400-800 tokens, with overlap).
- Embed everything. Store in pgvector. Index with HNSW.

**Afternoon (4 hrs)**
- Build `src/data/retriever.py`. Clean retriever class with hybrid search (vector + BM25 via Postgres full-text).
- Test queries: "knee MRI medical necessity", "preventive colonoscopy coverage", etc.
- Are results sensible? If not, fix chunking before moving on. Don't skip this.

**End of day:** can ask the retriever a question in natural language and get back the right policy/guideline chunks.

## Friday — intake agent + week wrap

**Morning (4 hrs)**
- Build the Intake Agent (starter in `src/agents/intake.py`).
- It takes a claim ID, parses the claim, normalizes codes to descriptions, fetches member history, returns a structured "claim packet" for downstream agents.
- Not an LLM agent yet. Deterministic. Next week I add the LLM layer.
- Write tests in `tests/test_intake.py`.

**Afternoon (3 hrs)**
- Write `docs/WEEK_1_RETRO.md`. What worked, what was harder than expected, what to fix.
- Update README with what's working.
- LinkedIn post: "Week 1 of building ClaimSight. Here's the data foundation." Include a snippet of code or a query result. Not promotional. Technical.

**Evening (1 hr)**
- Commit, push, tag `v0.1.0-foundation`.
- Take Saturday off. I'll need it.

**End of week:** real database with real (synthetic) claims. Working retriever. Claim intake pipeline. Tests. One LinkedIn post that signals I'm back and shipping.

## Failure modes to watch for

- **Spending all week on data and not shipping the agent.** If I'm behind by Thursday, cut the synthetic policy count to 8 and the guideline count to 10. Don't slip the agent week.
- **Over-engineering the schema.** Use the schema provided. Don't redesign it. Refactor in Week 9.
- **Trying to use real Medicare data.** SynPUF only. Don't get fancy.
- **Skipping tests.** Even one or two tests per module saves me in Week 6 when something breaks and I don't know why.

## What I'll have on Friday night

- Live GitHub repo
- Working Postgres with claims, providers, codes, embedded policies and guidelines
- Hybrid retriever
- Deterministic intake pipeline
- Tests
- One LinkedIn post
- Clear plan for Week 2 (the first real LLM agent)

Ship it.
