"""Intake Agent — the first stage of the ClaimSight pipeline.

Takes a claim_id, assembles a complete ClaimPacket with:
- The raw claim
- Member demographics
- Provider information
- Code descriptions (CPT, ICD-10) for everything coded numerically
- Recent member history

This agent is intentionally deterministic — no LLM call. It's pure data
assembly. Putting an LLM here would be wasteful and would introduce
non-determinism for no benefit. The LLM agents downstream consume the packet
this produces.

Design note: Specialist agents should never go back to the database for
primitives they can get from the packet. This keeps the agent graph simple
and makes evals reproducible.
"""

from __future__ import annotations

from src.data.code_lookup import lookup_cpt, lookup_icd10_batch, lookup_provider
from src.data.member_history import get_member, get_member_history
from src.db.connection import get_connection
from src.models.schemas import Claim, ClaimPacket


class IntakeError(Exception):
    """Raised when a claim cannot be loaded or assembled."""


def load_claim(claim_id: str) -> Claim:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                claim_id, member_id, provider_npi, service_date,
                place_of_service, primary_diagnosis, secondary_diagnoses,
                procedure_code, billed_amount, allowed_amount, submitted_at
            FROM claims
            WHERE claim_id = %s
            """,
            (claim_id,),
        )
        row = cur.fetchone()
    if not row:
        raise IntakeError(f"Claim not found: {claim_id}")
    # secondary_diagnoses comes back as a list (Postgres array) or None
    if row.get("secondary_diagnoses") is None:
        row["secondary_diagnoses"] = []
    return Claim(**row)


def build_packet(claim_id: str, *, history_lookback_days: int = 365) -> ClaimPacket:
    """Assemble a ClaimPacket for the given claim."""
    claim = load_claim(claim_id)

    member = get_member(claim.member_id)
    if not member:
        raise IntakeError(f"Member not found: {claim.member_id}")

    provider = lookup_provider(claim.provider_npi) if claim.provider_npi else None
    procedure = lookup_cpt(claim.procedure_code) if claim.procedure_code else None

    primary_dx = lookup_icd10_batch([claim.primary_diagnosis]) if claim.primary_diagnosis else []
    secondary_dxs = (
        lookup_icd10_batch(claim.secondary_diagnoses) if claim.secondary_diagnoses else []
    )

    history = get_member_history(
        claim.member_id,
        as_of=claim.service_date,
        lookback_days=history_lookback_days,
    )

    return ClaimPacket(
        claim=claim,
        member=member,
        provider=provider,
        procedure=procedure,
        primary_diagnosis_desc=primary_dx[0] if primary_dx else None,
        secondary_diagnosis_descs=secondary_dxs,
        member_history=history,
        history_lookback_days=history_lookback_days,
    )
