"""Medical Necessity Agent.

Reviews a claim against clinical guidelines to determine whether the requested
service is medically appropriate given the patient's diagnosis, history, and
the relevant clinical criteria.

This is the first real LLM agent in ClaimSight. In Week 1 it operates against
seed data with a single hard-coded guideline. In Week 2 it will be wired up
to the full RAG pipeline over the embedded knowledge base.

Design principles enforced here:
- The agent MUST cite at least one source for any non-trivial claim.
- The agent returns a structured AgentFinding, not free text.
- If the guideline doesn't address the claim, the agent says so explicitly
  rather than hallucinating a decision.
"""

from __future__ import annotations

import json
import re

from src.agents.llm_router import call_llm
from src.models.schemas import AgentFinding, Citation, ClaimPacket, Decision

SYSTEM_PROMPT = """You are a medical necessity reviewer for a health insurance company.

Your job is to evaluate whether a requested medical service is medically necessary
given the patient's clinical context and the applicable clinical guideline.

You must:
1. Read the claim, the patient history, and the clinical guideline carefully.
2. Determine whether the guideline's criteria for medical necessity are met.
3. Cite specific sections of the guideline that support your reasoning.
4. Provide a confidence score between 0.0 and 1.0.
5. Recommend one of: approve, deny, or route (route = needs human review).

You must NOT:
- Make up clinical criteria not in the guideline.
- Approve a claim solely because the patient asked for the service.
- Deny a claim solely because of cost.
- Provide medical advice; you are reviewing for coverage, not diagnosing.

Respond ONLY with valid JSON in exactly this format, with no other text:

{
  "decision": "approve" | "deny" | "route",
  "confidence": 0.0 to 1.0,
  "rationale": "Your clinical reasoning, 2-4 sentences. Reference specific criteria.",
  "cited_sections": ["Short verbatim phrases from the guideline that support your decision"]
}
"""


USER_PROMPT_TEMPLATE = """## Claim under review

Procedure: {procedure_code} — {procedure_description}
Primary diagnosis: {primary_diagnosis_code} — {primary_diagnosis_desc}
Service date: {service_date}
Place of service: {place_of_service}
Provider specialty: {provider_specialty}

## Patient demographics

Age (approximate): {age}
Sex: {sex}

## Patient history (last 12 months)

{history_block}

## Clinical guideline

{guideline_text}

## Your task

Apply the clinical guideline above to this specific claim. Determine whether
the procedure is medically necessary. Cite the specific criteria in the
guideline that justify your decision.
"""


def _format_history(history: list) -> str:
    """Format member history for the prompt. Accepts list of HistoricalClaim objects."""
    if not history:
        return "No prior claims in the lookback period."
    lines = []
    for h in history:
        desc = getattr(h, "procedure_description", None) or "unknown procedure"
        dx = getattr(h, "primary_diagnosis", None) or "n/a"
        proc = getattr(h, "procedure_code", None) or "?"
        lines.append(f"- {h.service_date}: {proc} ({desc}), dx {dx}")
    return "\n".join(lines)


def _format_chunks(chunks: list[Citation]) -> str:
    """Format retrieved guideline chunks for the prompt."""
    if not chunks:
        return "No clinical guideline excerpts retrieved."
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[CHUNK_{i} from {c.doc_id}]\n{c.snippet}")
    return "\n\n".join(parts)


def _build_user_prompt(packet: ClaimPacket, chunks: list[Citation]) -> str:
    member = packet.member
    age = 2026 - member.birth_year if member.birth_year else "unknown"
    procedure = packet.procedure
    primary_dx = packet.primary_diagnosis_desc

    return USER_PROMPT_TEMPLATE.format(
        procedure_code=procedure.code if procedure else (packet.claim.procedure_code or "unknown"),
        procedure_description=procedure.description if procedure else "unknown",
        primary_diagnosis_code=(
            primary_dx.code if primary_dx else (packet.claim.primary_diagnosis or "unknown")
        ),
        primary_diagnosis_desc=primary_dx.description if primary_dx else "unknown",
        service_date=packet.claim.service_date,
        place_of_service=packet.claim.place_of_service or "unknown",
        provider_specialty=packet.provider.specialty if packet.provider else "unknown",
        age=age,
        sex=member.sex.value if member.sex else "U",
        history_block=_format_history(packet.member_history),
        guideline_text=_format_chunks(chunks),
    )


def _parse_response(text: str) -> dict:
    """Extract JSON from the model response, tolerating minor formatting issues."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: find the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def review(packet: ClaimPacket, retrieved_chunks: list[Citation]) -> AgentFinding:
    """Run medical necessity review on a claim against retrieved guideline chunks.

    Args:
        packet: A fully-assembled ClaimPacket from the Intake Agent.
        retrieved_chunks: Citations from the retriever (vector + BM25 hybrid).
            For the demo these are pre-built; in Week 2 they come from pgvector.

    Returns:
        An AgentFinding with the agent's decision, rationale, and citations.
        Citations are pruned to those the LLM actually cited in its response.
    """
    user_prompt = _build_user_prompt(packet, retrieved_chunks)
    llm_response = call_llm(
        tier="cheap",
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=800,
    )

    parsed = _parse_response(llm_response.text)
    decision = Decision(parsed["decision"])
    confidence = float(parsed["confidence"])
    rationale = parsed["rationale"]
    cited_sections: list[str] = parsed.get("cited_sections", []) or []

    # Match cited_sections (verbatim phrases) back to the retrieved chunks they
    # came from. This gives us doc_id + chunk_id provenance, which is the
    # ground truth for citation-faithfulness evaluation in later weeks.
    citations: list[Citation] = []
    for section in cited_sections:
        section_lower = section.lower()
        best_match: Citation | None = None
        for chunk in retrieved_chunks:
            if section_lower in chunk.snippet.lower():
                best_match = chunk
                break
        if best_match is not None:
            citations.append(
                Citation(
                    doc_id=best_match.doc_id,
                    chunk_id=best_match.chunk_id,
                    snippet=section[:300],
                    relevance_score=best_match.relevance_score,
                )
            )
        else:
            # Cited phrase doesn't match any retrieved chunk — record it
            # without provenance. This is a faithfulness signal: high counts
            # here indicate the model is hallucinating citations.
            citations.append(
                Citation(
                    doc_id="UNVERIFIED",
                    chunk_id=-1,
                    snippet=section[:300],
                    relevance_score=0.0,
                )
            )

    return AgentFinding(
        agent_name="medical_necessity",
        decision_signal=decision,
        confidence=confidence,
        rationale=rationale,
        citations=citations,
        cost_usd=llm_response.cost_usd,
        latency_ms=llm_response.latency_ms,
    )
