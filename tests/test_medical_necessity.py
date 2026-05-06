"""Tests for the Medical Necessity Agent.

These tests use the LLM mock fallback (no API keys required) so they run in
CI without credentials. They verify the prompt-building, response parsing,
and citation-provenance logic — the deterministic parts of the agent.

Tests of LLM behavior itself live in the eval harness (`src/evals/`), not here.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

# Make sure no API keys are accidentally picked up — force the mock path
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

from src.agents.medical_necessity import _format_chunks, _format_history, _parse_response, review
from src.models.schemas import (
    Citation,
    Claim,
    ClaimPacket,
    CodeDescription,
    Decision,
    HistoricalClaim,
    Member,
    Provider,
    Sex,
)


def _build_test_packet(procedure_code: str = "73721") -> ClaimPacket:
    """Build a minimal valid ClaimPacket for testing."""
    return ClaimPacket(
        claim=Claim(
            claim_id="TEST-001",
            member_id="TEST-MBR-001",
            provider_npi="1234567890",
            service_date=date(2026, 4, 15),
            place_of_service="11",
            primary_diagnosis="M17.11",
            secondary_diagnoses=[],
            procedure_code=procedure_code,
            billed_amount=Decimal("1450.00"),
        ),
        member=Member(
            member_id="TEST-MBR-001",
            birth_year=1972,
            sex=Sex.F,
            state="MA",
            plan_type="PPO",
        ),
        provider=Provider(npi="1234567890", provider_name="Test Clinic", specialty="Radiology"),
        procedure=CodeDescription(code=procedure_code, description="Test procedure"),
        primary_diagnosis_desc=CodeDescription(code="M17.11", description="Knee OA"),
        secondary_diagnosis_descs=[],
        member_history=[],
    )


def _build_test_chunks() -> list[Citation]:
    return [
        Citation(
            doc_id="GUIDE-MSK-001",
            chunk_id=101,
            snippet=(
                "MRI of the knee is indicated for evaluation of suspected internal "
                "derangement, persistent unexplained pain, or osteoarthritis when "
                "conservative management (including physical therapy and NSAIDs) over "
                "a period of at least 6 weeks has failed to provide adequate relief."
            ),
            relevance_score=0.92,
        ),
        Citation(
            doc_id="GUIDE-MSK-001",
            chunk_id=102,
            snippet=(
                "For osteoarthritis (ICD-10 M17.x), advanced imaging such as MRI is "
                "generally reserved for cases where plain radiographs are inconclusive."
            ),
            relevance_score=0.88,
        ),
    ]


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


def test_format_history_handles_empty():
    assert "No prior claims" in _format_history([])


def test_format_history_renders_entries():
    history = [
        HistoricalClaim(
            claim_id="H1",
            service_date=date(2026, 1, 10),
            procedure_code="99213",
            procedure_description="Office visit",
            primary_diagnosis="M17.11",
        )
    ]
    formatted = _format_history(history)
    assert "99213" in formatted
    assert "Office visit" in formatted
    assert "M17.11" in formatted


def test_format_chunks_handles_empty():
    assert "No clinical guideline excerpts" in _format_chunks([])


def test_format_chunks_includes_doc_ids():
    chunks = _build_test_chunks()
    formatted = _format_chunks(chunks)
    assert "GUIDE-MSK-001" in formatted
    assert "CHUNK_1" in formatted
    assert "CHUNK_2" in formatted


# ---------------------------------------------------------------------------
# JSON parsing tolerance
# ---------------------------------------------------------------------------


def test_parse_response_plain_json():
    text = '{"decision": "approve", "confidence": 0.9, "rationale": "ok", "cited_sections": []}'
    parsed = _parse_response(text)
    assert parsed["decision"] == "approve"


def test_parse_response_markdown_fenced():
    text = '```json\n{"decision": "deny", "confidence": 0.8, "rationale": "no", "cited_sections": []}\n```'
    parsed = _parse_response(text)
    assert parsed["decision"] == "deny"


def test_parse_response_with_preamble():
    text = 'Sure! Here is the JSON:\n{"decision": "route", "confidence": 0.5, "rationale": "unclear", "cited_sections": []}'
    parsed = _parse_response(text)
    assert parsed["decision"] == "route"


# ---------------------------------------------------------------------------
# End-to-end review (uses mock LLM)
# ---------------------------------------------------------------------------


def test_review_returns_agent_finding():
    """The mock LLM returns a knee-MRI approval for our test packet."""
    packet = _build_test_packet(procedure_code="73721")
    chunks = _build_test_chunks()

    finding = review(packet, chunks)

    assert finding.agent_name == "medical_necessity"
    assert finding.decision_signal == Decision.APPROVE
    assert 0.0 <= finding.confidence <= 1.0
    assert finding.rationale  # non-empty
    assert finding.cost_usd == 0.0  # mock has zero cost
    assert finding.latency_ms >= 0


def test_review_resolves_citations_to_chunks():
    """When the LLM cites a verbatim phrase from a retrieved chunk, the agent
    should resolve that citation back to the chunk's doc_id and chunk_id."""
    packet = _build_test_packet(procedure_code="73721")
    chunks = _build_test_chunks()

    finding = review(packet, chunks)

    # At least one citation should resolve to a real chunk (not UNVERIFIED)
    resolved = [c for c in finding.citations if c.doc_id != "UNVERIFIED"]
    assert len(resolved) >= 1, "Expected at least one citation to resolve to a retrieved chunk"
    assert resolved[0].chunk_id in {101, 102}
    assert resolved[0].doc_id == "GUIDE-MSK-001"
