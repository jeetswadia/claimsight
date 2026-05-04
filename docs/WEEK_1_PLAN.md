# Week 1 — Foundations

**Goal by Friday:** Working data pipeline that ingests SynPUF claims into Postgres, with code mappings, member history queries, and a basic intake agent that can parse a claim and pull relevant context. No LLM agent loop yet — just the substrate.

**Why this week looks "boring":** Every weak agentic AI project skips this and tries to do agent stuff first. Yours won't, because the data layer is what makes the rest possible. This week is the foundation that lets weeks 3-8 actually work.

---

## Monday — Environment + repo

**Morning (3-4 hrs)**
- Push the scaffolded repo to GitHub. Public. MIT license.
- Set up Python 3.11 venv, install dependencies (pyproject.toml provided).
- Set up pre-commit hooks (ruff, black, mypy).
- Create Supabase project (free tier). Save connection string in `.env`.
- Verify pgvector extension is enabled.

**Afternoon (3-4 hrs)**
- Sign up for: Modal, Vercel, Groq (free tier), Langfuse Cloud or self-host.
- Get API keys. Store in `.env`. Document in README setup section.
- Run `scripts/00_verify_env.py` (provided) — confirms all services reachable.
- First commit. First push. Repo is live.

**End of day:** Repo exists, services connected, you can run a Python script that pings every service successfully.

---

## Tuesday — SynPUF acquisition + schema

**Morning (4 hrs)**
- Run `scripts/01_download_synpuf.py` (provided). This pulls a SynPUF sample.
- SynPUF is large; we only pull Sample 1 (~10K beneficiaries) which is plenty.
- Inspect the raw files. Document the schema in `docs/data_dictionary.md`.

**Afternoon (4 hrs)**
- Apply the database schema (`scripts/02_apply_schema.sql`, provided).
- Run `scripts/03_load_synpuf.py` to load beneficiaries, claims, providers.
- Spot-check with SQL: are claim counts reasonable, are joins working?

**End of day:** Postgres has real (synthetic) claims data. You can query "show me all claims for member X."

---

## Wednesday — Code mappings + provider data

**Morning (4 hrs)**
- Load CPT/ICD-10 reference data. Use the public CMS code sets.
- Load NPI provider directory subset (a few thousand providers is plenty for demo).
- Build `src/data/code_lookup.py` — utilities to translate codes to descriptions.

**Afternoon (4 hrs)**
- Synthesize 15 realistic policy documents covering common scenarios (preventive care, imaging, surgery, mental health, drugs, etc.). Use Claude or GPT to draft them, then edit for realism.
- Synthesize 20 clinical guideline summaries. Same approach.
- These go in `data/synthetic/policies/` and `data/synthetic/guidelines/` as markdown.

**End of day:** You can look up any code, find any provider, and you have a corpus of policies and guidelines to embed tomorrow.

---

## Thursday — Embeddings + retrieval

**Morning (4 hrs)**
- Set up the embeddings pipeline. Use `BAAI/bge-large-en-v1.5` via sentence-transformers (free, runs locally) or Voyage AI free tier.
- Chunk policies and guidelines (semantic chunking, 400-800 tokens, with overlap).
- Embed everything. Store in pgvector. Index with HNSW.

**Afternoon (4 hrs)**
- Build `src/data/retriever.py` — a clean retriever class with hybrid search (vector + BM25 via Postgres full-text).
- Test queries: "knee MRI medical necessity", "preventive colonoscopy coverage", etc.
- Are results sensible? If not, revisit chunking before moving on. Don't skip this.

**End of day:** You can ask the retriever a question in natural language and get back the right policy/guideline chunks.

---

## Friday — Intake agent + week wrap

**Morning (4 hrs)**
- Build the Intake Agent (starter provided in `src/agents/intake.py`).
- It takes a claim ID, parses the claim, normalizes codes to descriptions, fetches member history, returns a structured "claim packet" for downstream agents.
- This is *not* an LLM agent yet — it's deterministic. Next week we add the LLM layer.
- Write tests in `tests/test_intake.py`.

**Afternoon (3 hrs)**
- Write `docs/WEEK_1_RETRO.md` — what worked, what was harder than expected, what to fix.
- Update README with what's working.
- LinkedIn post: "Week 1 of building ClaimSight. Here's the data foundation." Include a snippet of code or a query result. Don't be promotional — be technical.

**Evening (1 hr)**
- Commit, push, tag `v0.1.0-foundation`.
- Take Saturday off. You'll need it.

**End of week:** A real database with real (synthetic) claims. A working retriever. A claim intake pipeline. Tests. One LinkedIn post that signals you're back and shipping.

---

## Failure modes to watch for

- **Spending all week on data and not shipping the agent.** If you're behind by Thursday, cut the synthetic policy count to 8 and the guideline count to 10. Don't slip the agent week.
- **Over-engineering the schema.** Use the schema provided. Don't redesign it. You can refactor in Week 9.
- **Trying to use real Medicare data.** SynPUF only. Don't get fancy.
- **Skipping tests.** Even one or two tests per module saves you in Week 6 when something breaks and you don't know why.

## What you'll have on Friday night

- Live GitHub repo
- Working Postgres with claims, providers, codes, embedded policies and guidelines
- Hybrid retriever
- Deterministic intake pipeline
- Tests
- One LinkedIn post
- A clear plan for Week 2 (the first real LLM agent)

Ship it.
