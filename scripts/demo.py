"""ClaimSight end-to-end demo.

Runs a claim through Intake → Medical Necessity Agent → formatted output.
Uses a built-in synthetic claim and mini-corpus so it works without database
setup. The only requirement is a GROQ_API_KEY in your .env file.

Usage:
    python scripts/demo.py
    python scripts/demo.py --claim knee-mri      # routine MRI, likely approve
    python scripts/demo.py --claim cosmetic      # cosmetic procedure, likely deny
    python scripts/demo.py --claim ambiguous     # edge case, likely route to human
    python scripts/demo.py --list                # show available scenarios
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Allow running this script directly without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from src.agents.medical_necessity import review
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

console = Console()


# ============================================================================
# Built-in synthetic scenarios
# ============================================================================

SCENARIOS = {
    "knee-mri": {
        "description": "MRI of knee for chronic pain after conservative treatment failure",
        "claim": Claim(
            claim_id="DEMO-CLAIM-001",
            member_id="DEMO-MBR-001",
            provider_npi="1234567890",
            service_date=date(2026, 4, 15),
            place_of_service="11",  # office
            primary_diagnosis="M17.11",  # Unilateral primary osteoarthritis, right knee
            secondary_diagnoses=["M25.561"],  # Pain in right knee
            procedure_code="73721",  # MRI lower extremity without contrast
            billed_amount=Decimal("1450.00"),
        ),
        "procedure": CodeDescription(
            code="73721",
            description="MRI any joint of lower extremity without contrast material",
            category="Radiology",
        ),
        "primary_dx": CodeDescription(
            code="M17.11",
            description="Unilateral primary osteoarthritis, right knee",
            category="Musculoskeletal",
        ),
        "secondary_dxs": [
            CodeDescription(
                code="M25.561",
                description="Pain in right knee",
                category="Musculoskeletal",
            )
        ],
        "history": [
            HistoricalClaim(
                claim_id="DEMO-HIST-001",
                service_date=date(2026, 1, 10),
                procedure_code="99213",
                procedure_description="Office visit, established patient, level 3",
                primary_diagnosis="M17.11",
            ),
            HistoricalClaim(
                claim_id="DEMO-HIST-002",
                service_date=date(2026, 2, 15),
                procedure_code="97110",
                procedure_description="Therapeutic exercises (physical therapy)",
                primary_diagnosis="M17.11",
            ),
            HistoricalClaim(
                claim_id="DEMO-HIST-003",
                service_date=date(2026, 3, 22),
                procedure_code="99213",
                procedure_description="Office visit, established patient, level 3",
                primary_diagnosis="M17.11",
            ),
        ],
        "chunks": [
            Citation(
                doc_id="GUIDE-MSK-001",
                chunk_id=101,
                snippet=(
                    "MRI of the knee is indicated for evaluation of suspected internal "
                    "derangement, persistent unexplained pain, or osteoarthritis when "
                    "conservative management (including physical therapy and NSAIDs) over "
                    "a period of at least 6 weeks has failed to provide adequate relief. "
                    "MRI is also indicated when surgical intervention is being considered."
                ),
                relevance_score=0.92,
            ),
            Citation(
                doc_id="GUIDE-MSK-001",
                chunk_id=102,
                snippet=(
                    "For osteoarthritis (ICD-10 M17.x), advanced imaging such as MRI is "
                    "generally reserved for cases where plain radiographs are inconclusive, "
                    "where there is suspicion of meniscal injury, or where conservative "
                    "treatment has failed. Documentation should reflect prior trial of "
                    "conservative therapy."
                ),
                relevance_score=0.88,
            ),
            Citation(
                doc_id="GUIDE-MSK-002",
                chunk_id=215,
                snippet=(
                    "Physical therapy for knee osteoarthritis typically requires a "
                    "minimum of 4-6 weeks of supervised therapy with documented response "
                    "assessment before escalation to advanced imaging or surgical consultation."
                ),
                relevance_score=0.71,
            ),
        ],
    },
    "cosmetic": {
        "description": "Rhinoplasty for purely cosmetic reasons (no functional indication)",
        "claim": Claim(
            claim_id="DEMO-CLAIM-002",
            member_id="DEMO-MBR-002",
            provider_npi="1234567890",
            service_date=date(2026, 4, 20),
            place_of_service="22",  # outpatient hospital
            primary_diagnosis="Z41.1",  # Encounter for cosmetic surgery
            secondary_diagnoses=[],
            procedure_code="30400",  # Rhinoplasty, primary
            billed_amount=Decimal("8500.00"),
        ),
        "procedure": CodeDescription(
            code="30400",
            description="Rhinoplasty, primary; lateral and alar cartilages and/or elevation of nasal tip",
            category="Surgery",
        ),
        "primary_dx": CodeDescription(
            code="Z41.1",
            description="Encounter for cosmetic surgery",
            category="Factors influencing health status",
        ),
        "secondary_dxs": [],
        "history": [],
        "chunks": [
            Citation(
                doc_id="POLICY-COSMETIC-001",
                chunk_id=301,
                snippet=(
                    "Cosmetic procedures performed solely to improve appearance, without "
                    "functional impairment, are not covered benefits under this plan. "
                    "Rhinoplasty is covered only when documented to correct a functional "
                    "impairment such as obstructed nasal breathing (deviated septum, J34.2) "
                    "or to repair traumatic injury."
                ),
                relevance_score=0.95,
            ),
            Citation(
                doc_id="POLICY-COSMETIC-001",
                chunk_id=302,
                snippet=(
                    "ICD-10 code Z41.1 (Encounter for cosmetic surgery) is explicitly "
                    "excluded from coverage. Procedures coded with Z41.1 as the primary "
                    "diagnosis should be denied."
                ),
                relevance_score=0.94,
            ),
        ],
    },
    "ambiguous": {
        "description": "Sleep study for fatigue — borderline indication, incomplete history",
        "claim": Claim(
            claim_id="DEMO-CLAIM-003",
            member_id="DEMO-MBR-003",
            provider_npi="1234567890",
            service_date=date(2026, 5, 1),
            place_of_service="11",
            primary_diagnosis="R53.83",  # Other fatigue
            secondary_diagnoses=[],
            procedure_code="95810",  # Polysomnography, sleep study
            billed_amount=Decimal("2200.00"),
        ),
        "procedure": CodeDescription(
            code="95810",
            description="Polysomnography; age 6 years or older, sleep staging with 4+ parameters",
            category="Medicine",
        ),
        "primary_dx": CodeDescription(
            code="R53.83",
            description="Other fatigue",
            category="Symptoms and signs",
        ),
        "secondary_dxs": [],
        "history": [],
        "chunks": [
            Citation(
                doc_id="GUIDE-SLEEP-001",
                chunk_id=401,
                snippet=(
                    "Polysomnography (CPT 95810) is indicated for evaluation of suspected "
                    "obstructive sleep apnea, narcolepsy, or other defined sleep disorders. "
                    "Indication requires documented symptoms such as witnessed apnea, "
                    "habitual snoring, excessive daytime somnolence, or unexplained fatigue "
                    "with risk factors (BMI > 30, hypertension, etc.)."
                ),
                relevance_score=0.78,
            ),
            Citation(
                doc_id="GUIDE-SLEEP-001",
                chunk_id=402,
                snippet=(
                    "ICD-10 R53.83 (Other fatigue) alone is not typically sufficient to "
                    "establish medical necessity for polysomnography. Additional clinical "
                    "documentation supporting suspicion of a specific sleep disorder is "
                    "generally required."
                ),
                relevance_score=0.85,
            ),
        ],
    },
}


def build_packet(scenario_key: str) -> ClaimPacket:
    """Build a ClaimPacket from a scenario without touching the database."""
    s = SCENARIOS[scenario_key]
    member = Member(
        member_id=s["claim"].member_id,
        birth_year=1972,
        sex=Sex.F,
        state="MA",
        plan_type="PPO",
        coverage_start=date(2024, 1, 1),
    )
    provider = Provider(
        npi="1234567890",
        provider_name="Demo Medical Group",
        specialty="Internal Medicine",
        state="MA",
    )
    return ClaimPacket(
        claim=s["claim"],
        member=member,
        provider=provider,
        procedure=s["procedure"],
        primary_diagnosis_desc=s["primary_dx"],
        secondary_diagnosis_descs=s["secondary_dxs"],
        member_history=s["history"],
    )


# ============================================================================
# Pretty output
# ============================================================================

DECISION_STYLES = {
    Decision.APPROVE: ("green", "✓ APPROVE"),
    Decision.DENY: ("red", "✗ DENY"),
    Decision.ROUTE: ("yellow", "→ ROUTE TO HUMAN"),
}


def render_packet(packet: ClaimPacket) -> Panel:
    """Render the claim packet as a Rich panel."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim cyan", justify="right")
    table.add_column()

    table.add_row("Claim ID", packet.claim.claim_id)
    table.add_row("Service date", str(packet.claim.service_date))
    if packet.procedure:
        table.add_row(
            "Procedure",
            f"[bold]{packet.procedure.code}[/bold] — {packet.procedure.description}",
        )
    if packet.primary_diagnosis_desc:
        table.add_row(
            "Primary diagnosis",
            f"[bold]{packet.primary_diagnosis_desc.code}[/bold] — "
            f"{packet.primary_diagnosis_desc.description}",
        )
    for dx in packet.secondary_diagnosis_descs:
        table.add_row("Secondary dx", f"{dx.code} — {dx.description}")
    if packet.claim.billed_amount:
        table.add_row("Billed amount", f"${packet.claim.billed_amount:,.2f}")
    if packet.member_history:
        history_text = "\n".join(
            f"  • {h.service_date}: {h.procedure_description or h.procedure_code}"
            for h in packet.member_history[:5]
        )
        table.add_row("History (recent)", history_text)
    return Panel(table, title="[bold]Claim Packet[/bold]", border_style="blue")


def render_finding(finding) -> Panel:
    """Render the agent finding as a Rich panel."""
    color, label = DECISION_STYLES[finding.decision_signal]

    body = Table(show_header=False, box=None, padding=(0, 1))
    body.add_column(style="dim cyan", justify="right")
    body.add_column()

    body.add_row("Decision", Text(label, style=f"bold {color}"))
    body.add_row("Confidence", f"{finding.confidence:.0%}")
    body.add_row("Rationale", finding.rationale)
    body.add_row("", "")
    body.add_row("Cost", f"${finding.cost_usd:.6f}")
    body.add_row("Latency", f"{finding.latency_ms} ms")
    body.add_row("Citations", f"{len(finding.citations)} chunk(s) cited")

    if finding.citations:
        body.add_row("", "")
        for c in finding.citations:
            snippet = c.snippet[:140] + ("..." if len(c.snippet) > 140 else "")
            body.add_row(
                f"[dim]chunk {c.chunk_id}[/dim]",
                f"[dim italic]{snippet}[/dim italic]",
            )

    return Panel(
        body,
        title=f"[bold]Medical Necessity Agent[/bold]  ([{color}]{label}[/{color}])",
        border_style=color,
    )


def list_scenarios() -> None:
    table = Table(title="Available demo scenarios")
    table.add_column("Key", style="cyan")
    table.add_column("Description")
    for k, v in SCENARIOS.items():
        table.add_row(k, v["description"])
    console.print(table)


def run(scenario_key: str) -> int:
    if scenario_key not in SCENARIOS:
        console.print(f"[red]Unknown scenario: {scenario_key}[/red]")
        list_scenarios()
        return 1

    console.print()
    console.print(Rule(f"[bold cyan]ClaimSight Demo — {scenario_key}[/bold cyan]", style="cyan"))
    console.print(f"[dim]{SCENARIOS[scenario_key]['description']}[/dim]\n")

    packet = build_packet(scenario_key)
    console.print(render_packet(packet))
    console.print()

    chunks = SCENARIOS[scenario_key]["chunks"]
    console.print(
        f"[dim]Retrieved {len(chunks)} guideline chunk(s) "
        f"(in production this would be a vector + BM25 hybrid search)[/dim]\n"
    )

    with console.status("[cyan]Running medical necessity review...", spinner="dots"):
        try:
            finding = review(packet, chunks)
        except Exception as e:
            console.print(f"[red]Agent call failed: {e}[/red]")
            console.print("[yellow]Hint: make sure GROQ_API_KEY is set in your .env file.[/yellow]")
            return 1

    console.print(render_finding(finding))
    console.print()
    console.print(
        Rule(
            f"[dim]Total cost: ${finding.cost_usd:.6f}  ·  "
            f"Total latency: {finding.latency_ms} ms[/dim]",
            style="dim",
        )
    )
    console.print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ClaimSight end-to-end demo")
    parser.add_argument(
        "--claim",
        default="knee-mri",
        help="Scenario key (default: knee-mri). Use --list to see options.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return 0

    return run(args.claim)


if __name__ == "__main__":
    sys.exit(main())
