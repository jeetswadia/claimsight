# ADR-0004: Synthetic data only

Date: 2026-05-05
Status: Accepted

## Context

To demonstrate ClaimSight, I need claims data, member data, provider data, and clinical knowledge. Real healthcare data is regulated under HIPAA and contains PHI (protected health information). Even "de-identified" datasets carry re-identification risk and licensing constraints.

A portfolio project does not justify any PHI exposure, however small.

## Decision

Synthetic data only, end to end:

- **Claims and members.** CMS SynPUF (Medicare Claims Synthetic Public Use Files). Fully synthetic, public, no re-identification risk. Fallback: Synthea-generated FHIR claims if SynPUF URLs rotate.
- **Provider data.** NPI Registry (public, but providers are real organizations. Their public registry data is non-sensitive).
- **Policies and clinical guidelines.** Synthesized from public materials (CMS Local Coverage Determinations, National Coverage Determinations, public clinical guideline summaries). Clearly labeled as synthetic in every document.

Documented prominently in the README and in writeups. Framed as a credibility marker, not a limitation.

## Alternatives considered

**Use a partner organization's de-identified data.** Out of scope for an independent portfolio project. Introduces compliance overhead.

**Scrape clinical guidelines from copyrighted sources.** Hard no. Copyright and ethical issues.

**Use a publicly available real-claims dataset (e.g., MIMIC).** MIMIC is for hospital ICU data, not insurance claims. Wrong shape. Other "real claims" datasets either don't exist publicly or carry licensing restrictions incompatible with public portfolio use.

## Consequences

**Enables**
- Zero PHI exposure
- Public repo, public demo, public writeups. No compliance review needed.
- Strong story to tell in interviews ("I built this without ever touching real patient data")

**Costs**
- Synthetic data has known statistical artifacts that can leak into model evaluation. I document this in eval reports.
- Fraud detection model is limited by the synthetic generator's distribution. I frame the model as a methodology demonstration, not a deployable asset.
- Synthesized policies are necessarily simplified. Real insurer policies are 100+ pages of legalese.

**Reversible?** Not meaningfully. This is a project-defining constraint and I lean into it.
