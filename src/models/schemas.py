"""Domain models for claims and adjudication."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class Decision(StrEnum):
    APPROVE = "approve"
    DENY = "deny"
    ROUTE = "route"  # route to human reviewer


class Sex(StrEnum):
    M = "M"
    F = "F"
    U = "U"


class Member(BaseModel):
    member_id: str
    birth_year: int | None = None
    sex: Sex | None = None
    state: str | None = None
    plan_type: str | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None


class Provider(BaseModel):
    npi: str
    provider_name: str
    specialty: str | None = None
    state: str | None = None


class Claim(BaseModel):
    claim_id: str
    member_id: str
    provider_npi: str | None = None
    service_date: date
    place_of_service: str | None = None
    primary_diagnosis: str | None = None
    secondary_diagnoses: list[str] = Field(default_factory=list)
    procedure_code: str | None = None
    billed_amount: Decimal | None = None
    allowed_amount: Decimal | None = None
    submitted_at: datetime | None = None


class CodeDescription(BaseModel):
    code: str
    description: str
    category: str | None = None


class HistoricalClaim(BaseModel):
    """A simplified historical claim used in member-history summaries."""

    claim_id: str
    service_date: date
    procedure_code: str | None = None
    procedure_description: str | None = None
    primary_diagnosis: str | None = None


class ClaimPacket(BaseModel):
    """The structured package the Intake Agent produces.

    Downstream specialist agents consume this. It contains everything they need
    to do their job without going back to the database for primitives.
    """

    claim: Claim
    member: Member
    provider: Provider | None = None
    procedure: CodeDescription | None = None
    primary_diagnosis_desc: CodeDescription | None = None
    secondary_diagnosis_descs: list[CodeDescription] = Field(default_factory=list)
    member_history: list[HistoricalClaim] = Field(default_factory=list)
    history_lookback_days: int = 365


class Citation(BaseModel):
    doc_id: str
    chunk_id: int
    snippet: str
    relevance_score: float


class AgentFinding(BaseModel):
    """The output shape every specialist agent returns."""

    agent_name: str
    decision_signal: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    citations: list[Citation] = Field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


class AdjudicationResult(BaseModel):
    """The final output of the agent graph."""

    claim_id: str
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    findings: list[AgentFinding] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    version_tag: str = "v0.1.0"
