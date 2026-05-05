# Security

## Reporting a vulnerability

If you find a security issue, please email the maintainer directly rather than opening a public issue.

Contact: jeet.swadia@example.com (replace with real email before publishing)

## Scope

This is a portfolio project, not a production service. Security expectations are correspondingly modest:

- Don't commit secrets. The `.gitignore` and pre-commit hooks help, but ultimately the developer is responsible.
- Don't introduce real PHI under any circumstances.
- LLM prompts that could leak system internals (e.g., system prompts, internal tool schemas) should be reviewed before merging.

## What ClaimSight does NOT do

- Authentication / authorization (no real users)
- HIPAA compliance (no PHI involved)
- Production-grade encryption at rest (relies on database provider defaults)

These are intentional scope choices for a portfolio project. A real production system would handle all of these, and the writeup discusses what those would look like.
