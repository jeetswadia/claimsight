"""Tests for the Intake Agent.

These tests assume a Postgres test database with at least one fixture claim.
Run scripts/03_load_synpuf.py first, then run pytest.

For now these are smoke tests — Week 1 ends with at least basic assertions
that the pipeline runs end-to-end on real data.
"""

from __future__ import annotations

import os

import pytest

from src.agents.intake import IntakeError, build_packet, load_claim
from src.models.schemas import ClaimPacket

# A claim_id loaded by 03_load_synpuf.py — set this once data is loaded.
# Override via env for CI: TEST_CLAIM_ID=...
SAMPLE_CLAIM_ID = os.getenv("TEST_CLAIM_ID", "")


@pytest.mark.skipif(not SAMPLE_CLAIM_ID, reason="TEST_CLAIM_ID not set")
def test_load_claim_returns_claim():
    claim = load_claim(SAMPLE_CLAIM_ID)
    assert claim.claim_id == SAMPLE_CLAIM_ID
    assert claim.member_id
    assert claim.service_date


@pytest.mark.skipif(not SAMPLE_CLAIM_ID, reason="TEST_CLAIM_ID not set")
def test_build_packet_returns_complete_packet():
    packet = build_packet(SAMPLE_CLAIM_ID)
    assert isinstance(packet, ClaimPacket)
    assert packet.claim.claim_id == SAMPLE_CLAIM_ID
    assert packet.member.member_id == packet.claim.member_id


def test_load_claim_raises_on_missing():
    with pytest.raises(IntakeError, match="not found"):
        load_claim("definitely-does-not-exist-12345")
