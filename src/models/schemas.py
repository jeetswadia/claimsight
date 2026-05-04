"""Domain models for claims and adjudication."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    ROUTE = "route"  # route to human reviewer


class Sex(str, Enum):
    M = "M"
    F = "F"
    U = "U"


class Member(BaseModel):
    member_id: str
    birth_year: Optional[int] = None
    sex: Optional[Sex] = None
    state: Optional[str] = None
    plan_type: Optional[str] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None


class Provider(BaseModel):
    npi: str
    provider_name: str
    specialty: Optional[str] = None
    state: Optional[str] = None


class Claim(BaseModel):
    claim_id: str
    member_id: str
    provider_npi: Optional[str] = None
    service_date: date
    place_of_service: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: list[str] = Field(default_factory=list)
    procedure_code: Optional[str] = None
    billed_amount: Optional[Decimal] = None
    allowed_amount: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None


class CodeDescription(BaseModel):
    code: str
    description: str
    category: Optional[str] = None


class HistoricalClaim(BaseModel):
    """A simplified historical claim used in member-history summaries."""

    claim_id: str
    service_date: date
    procedure_code: Optional[str] = None
    procedure_description: Optional[str] = None
    primary_diagnosis: Optional[str] = None


class ClaimPacket(BaseModel):
    """The structured package the Intake Agent produces.

    Downstream specialist agents consume this. It contains everything they need
    to do their job without going back to the database for primitives.
    """

    claim: Claim
    member: Member
    provider: Optional[Provider] = None
    procedure: Optional[CodeDescription] = None
    primary_diagnosis_desc: Optional[CodeDescription] = None
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
