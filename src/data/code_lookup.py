"""Lookup utilities for CPT, ICD-10, and NPI."""

from __future__ import annotations

from src.db.connection import get_connection
from src.models.schemas import CodeDescription, Provider


def lookup_cpt(code: str) -> CodeDescription | None:
    if not code:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT code, description, category FROM cpt_codes WHERE code = %s",
            (code,),
        )
        row = cur.fetchone()
    return CodeDescription(**row) if row else None


def lookup_icd10(code: str) -> CodeDescription | None:
    if not code:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT code, description, chapter AS category FROM icd10_codes WHERE code = %s",
            (code,),
        )
        row = cur.fetchone()
    return CodeDescription(**row) if row else None


def lookup_provider(npi: str) -> Provider | None:
    if not npi:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT npi, provider_name, specialty, state
            FROM providers WHERE npi = %s
            """,
            (npi,),
        )
        row = cur.fetchone()
    return Provider(**row) if row else None


def lookup_icd10_batch(codes: list[str]) -> list[CodeDescription]:
    """Look up many ICD-10 codes in one query. Returns only those found."""
    codes = [c for c in codes if c]
    if not codes:
        return []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT code, description, chapter AS category
            FROM icd10_codes WHERE code = ANY(%s)
            """,
            (codes,),
        )
        rows = cur.fetchall()
    return [CodeDescription(**r) for r in rows]
