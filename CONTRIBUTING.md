# Contributing

Thanks for your interest. ClaimSight is primarily a portfolio project, but issues, discussions, and PRs are welcome.

## Ground rules

1. **No real PHI.** Ever. Synthetic data only (CMS SynPUF, Synthea). Any PR that introduces or hints at real patient data gets rejected.
2. **No overclaiming.** Don't add language calling this "production-ready." It's production-shaped. The distinction matters.
3. **Tests for new code.** New modules need at least smoke tests. New agents need eval coverage.
4. **Citations matter.** If an agent makes a claim, it must cite a source. No exceptions.

## Dev setup

```bash
git clone https://github.com/jeetsswadia/claimsight.git
cd claimsight
python -m venv .venv && source .venv/bin/activate
make install
make verify
```

## Workflow

1. Branch: `git checkout -b feat/short-description` or `fix/short-description`
2. Make your changes
3. Run `make format && make lint && make test`
4. Commit with a clear message (see below)
5. Push and open a PR

## Commit messages

Conventional Commits style:

- `feat: add medical necessity agent`
- `fix: handle missing CPT codes in intake`
- `docs: clarify SynPUF acquisition step`
- `test: add coverage for retriever hybrid search`
- `refactor: extract chunking into separate module`
- `chore: bump dependencies`

Keep the subject line under 72 characters. Use the body for the *why*.

## Code style

- Black, line length 100
- Ruff for linting
- Type hints on all new public functions
- Docstrings on agents, public functions, and non-obvious logic

## Reporting issues

Use the issue templates. Include:

- What you were trying to do
- What happened
- What you expected
- Reproducible steps if relevant
- Environment (OS, Python version, Postgres version)

## Areas where help is welcome

- Adding new specialist agents (e.g., DRG validation)
- Improving eval methodology
- Better synthetic policy and guideline corpora
- Documentation improvements
