# Changelog

All notable changes to ClaimSight are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffold
- Postgres + pgvector schema for claims, members, providers, knowledge base, agent traces
- Pydantic schemas for the full pipeline (Claim, ClaimPacket, AgentFinding, AdjudicationResult)
- CPT/ICD-10/NPI lookup utilities
- Member history retrieval
- Intake Agent (deterministic, non-LLM)
- LLM router with two tiers (Groq for cheap, Anthropic for smart) and a deterministic mock fallback when keys are missing
- Medical necessity agent with citation provenance back to retrieved chunks
- End-to-end demo script with three scenarios (approve, deny, route) that runs without DB or API keys
- Environment verification script
- SynPUF download script with Synthea fallback
- Architecture Decision Records (ADRs 0001-0004)
- CI workflow (ruff, black, mypy, pytest with Postgres service)
- Makefile for common dev commands
- Pre-commit hooks
- Setup documentation
- Contributing guide

## [0.1.0-foundation] - planned end of Week 1

First milestone tag: data layer and intake working end-to-end.
