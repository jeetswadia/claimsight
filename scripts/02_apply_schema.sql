-- ClaimSight database schema
-- Apply with: psql $DATABASE_URL -f scripts/02_apply_schema.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- Reference data
-- ============================================================================

CREATE TABLE IF NOT EXISTS cpt_codes (
    code        TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    category    TEXT
);

CREATE TABLE IF NOT EXISTS icd10_codes (
    code        TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    chapter     TEXT
);

CREATE TABLE IF NOT EXISTS providers (
    npi              TEXT PRIMARY KEY,
    provider_name    TEXT NOT NULL,
    specialty        TEXT,
    state            TEXT,
    enrolled_since   DATE
);

-- ============================================================================
-- Claims data (loaded from SynPUF)
-- ============================================================================

CREATE TABLE IF NOT EXISTS members (
    member_id          TEXT PRIMARY KEY,
    birth_year         INT,
    sex                TEXT CHECK (sex IN ('M', 'F', 'U')),
    state              TEXT,
    plan_type          TEXT,
    coverage_start     DATE,
    coverage_end       DATE
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id           TEXT PRIMARY KEY,
    member_id          TEXT NOT NULL REFERENCES members(member_id),
    provider_npi       TEXT REFERENCES providers(npi),
    service_date       DATE NOT NULL,
    place_of_service   TEXT,
    primary_diagnosis  TEXT,
    secondary_diagnoses TEXT[],
    procedure_code     TEXT,
    billed_amount      NUMERIC(10, 2),
    allowed_amount     NUMERIC(10, 2),
    submitted_at       TIMESTAMPTZ DEFAULT NOW(),
    -- For ground truth in evals; populated synthetically
    ground_truth_decision TEXT CHECK (ground_truth_decision IN ('approve', 'deny', 'route'))
);

CREATE INDEX IF NOT EXISTS idx_claims_member ON claims(member_id);
CREATE INDEX IF NOT EXISTS idx_claims_service_date ON claims(service_date);
CREATE INDEX IF NOT EXISTS idx_claims_procedure ON claims(procedure_code);

-- ============================================================================
-- Knowledge base (policies + clinical guidelines, embedded)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_documents (
    doc_id        TEXT PRIMARY KEY,
    doc_type      TEXT NOT NULL CHECK (doc_type IN ('policy', 'guideline')),
    title         TEXT NOT NULL,
    source        TEXT,
    full_text     TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id      BIGSERIAL PRIMARY KEY,
    doc_id        TEXT NOT NULL REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
    chunk_index   INT NOT NULL,
    chunk_text    TEXT NOT NULL,
    -- bge-large-en-v1.5 produces 1024-dim vectors
    embedding     vector(1024),
    -- For BM25 hybrid search via tsvector
    tsv           tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON knowledge_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON knowledge_chunks USING GIN(tsv);
-- Build HNSW index after embeddings are loaded; empty index can be slow to query
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON knowledge_chunks
--     USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- Agent run traces (for eval harness + debugging)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    final_decision  TEXT,
    confidence      NUMERIC(3, 2),
    total_cost_usd  NUMERIC(8, 4),
    total_latency_ms INT,
    version_tag     TEXT
);

CREATE TABLE IF NOT EXISTS agent_steps (
    step_id         BIGSERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,
    step_index      INT NOT NULL,
    input           JSONB,
    output          JSONB,
    cited_doc_ids   TEXT[],
    cost_usd        NUMERIC(8, 4),
    latency_ms      INT,
    started_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_steps_run ON agent_steps(run_id);

-- ============================================================================
-- Eval results
-- ============================================================================

CREATE TABLE IF NOT EXISTS eval_runs (
    eval_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_tag    TEXT NOT NULL,
    run_at         TIMESTAMPTZ DEFAULT NOW(),
    n_claims       INT,
    metrics        JSONB,
    notes          TEXT
);
