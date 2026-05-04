"""Retrieve member history (recent claims) for a given member."""
from __future__ import annotations

from datetime import date, timedelta

from src.db.connection import get_connection
from src.models.schemas import HistoricalClaim, Member


def get_member(member_id: str) -> Member | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        row = cur.fetchone()
    return Member(**row) if row else None


def get_member_history(
    member_id: str,
    *,
    as_of: date,
    lookback_days: int = 365,
    limit: int = 50,
) -> list[HistoricalClaim]:
    """Return historical claims for a member, most recent first."""
    cutoff = as_of - timedelta(days=lookback_days)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.claim_id,
                c.service_date,
                c.procedure_code,
                cpt.description AS procedure_description,
                c.primary_diagnosis
            FROM claims c
            LEFT JOIN cpt_codes cpt ON cpt.code = c.procedure_code
            WHERE c.member_id = %s
              AND c.service_date >= %s
              AND c.service_date < %s
            ORDER BY c.service_date DESC
            LIMIT %s
            """,
            (member_id, cutoff, as_of, limit),
        )
        rows = cur.fetchall()
    return [HistoricalClaim(**r) for r in rows]
