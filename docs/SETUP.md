# Setup

Zero to a working ClaimSight dev environment in ~30 minutes.

If you just want to run the demo, skip this whole doc and run:

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight && pip install -e . && python scripts/demo.py
```

The rest of this doc is for the full dev environment with database and real LLMs.

## Prerequisites

- Python 3.11 or newer
- Git
- Postgres with pgvector (Supabase free tier works)
- Free accounts on:
  - [Groq](https://console.groq.com/) for LLM (free tier)
  - [Anthropic](https://console.anthropic.com/) for LLM (small spend)
  - [Langfuse](https://cloud.langfuse.com/) for observability (free tier)

## 1. Clone and install

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## 2. Postgres with pgvector

### Option A: Supabase (recommended, free tier)

1. Create a free project at [supabase.com](https://supabase.com/)
2. In the SQL editor: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Copy the connection string from Settings → Database → Connection string (URI mode)

### Option B: Local Postgres

```bash
docker run -d \
  --name claimsight-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=claimsight \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

Connection string: `postgresql://postgres:postgres@localhost:5432/claimsight`

## 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Supabase or local Postgres |
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `LANGFUSE_PUBLIC_KEY` | cloud.langfuse.com → Settings → API Keys |
| `LANGFUSE_SECRET_KEY` | same place |

The cost guardrails (`MAX_DAILY_USD`, `MAX_PER_CLAIM_USD`) are conservative defaults. Tune as needed.

## 4. Verify

```bash
make verify
```

Green checkmarks for Postgres (with pgvector), Groq, and Anthropic. If anything fails, fix it before moving on.

## 5. Apply schema

```bash
make db-init
```

Creates tables for claims, members, providers, knowledge documents (with vector embeddings), agent run traces, and eval results.

## 6. Load synthetic claims

```bash
make data-download   # 2-5 minutes depending on connection
make data-load       # 5-10 minutes
```

Pulls a CMS SynPUF sample (~10K synthetic Medicare beneficiaries, no PHI risk) and loads it into Postgres.

If the SynPUF download fails (CMS occasionally rotates URLs), the script docstring has the [Synthea](https://github.com/synthetichealth/synthea) fallback that generates synthetic FHIR claims locally.

## 7. Tests

```bash
make test
```

Smoke tests should pass. If `TEST_CLAIM_ID` isn't set, several tests skip. That's expected on first setup. After data loading, set it to any real claim_id from the loaded data.

## 8. You're ready

Next: [docs/WEEK_1_PLAN.md](WEEK_1_PLAN.md) for the day-by-day build plan.

## Troubleshooting

**"vector extension does not exist"**
Postgres has the vector extension package, but it's not enabled. Run `CREATE EXTENSION vector;` in your database.

**"DATABASE_URL not set"**
Your `.env` isn't being loaded, or you forgot to copy from `.env.example`. Check that `.env` exists in the repo root.

**Groq returns 401**
API key is wrong or expired. Generate a new one.

**Anthropic returns 401**
Same. Regenerate the key.

**SynPUF download fails**
CMS rotates URLs occasionally. See the script docstring for the Synthea fallback. Works entirely locally.
