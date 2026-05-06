"""Verify all required services and credentials are reachable.

Run this on Day 1 before doing anything else. If this passes, you have a
working development environment. If it fails, fix the failure before moving on.

Usage:
    python scripts/00_verify_env.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def check_env_var(name: str) -> Check:
    val = os.getenv(name)
    if not val:
        return Check(name, False, "not set in .env")
    return Check(name, True, f"set ({len(val)} chars)")


def check_database() -> Check:
    try:
        import psycopg

        url = os.getenv("DATABASE_URL")
        if not url:
            return Check("Postgres connection", False, "DATABASE_URL not set")
        with psycopg.connect(url, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0].split(",")[0]
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            has_pgvector = cur.fetchone() is not None
        detail = f"{version}, pgvector={'yes' if has_pgvector else 'NO — enable it'}"
        return Check("Postgres connection", has_pgvector, detail)
    except Exception as e:
        return Check("Postgres connection", False, f"failed: {e}")


def check_groq() -> Check:
    try:
        import httpx

        key = os.getenv("GROQ_API_KEY")
        if not key:
            return Check("Groq API", False, "GROQ_API_KEY not set")
        r = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if r.status_code == 200:
            models = len(r.json().get("data", []))
            return Check("Groq API", True, f"reachable, {models} models available")
        return Check("Groq API", False, f"HTTP {r.status_code}")
    except Exception as e:
        return Check("Groq API", False, f"failed: {e}")


def check_anthropic() -> Check:
    try:
        import httpx

        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return Check("Anthropic API", False, "ANTHROPIC_API_KEY not set")
        # Cheap ping: just hit the messages endpoint with a tiny request
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "hi"}],
            },
            timeout=15,
        )
        if r.status_code == 200:
            return Check("Anthropic API", True, "reachable, key valid")
        return Check("Anthropic API", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        return Check("Anthropic API", False, f"failed: {e}")


def check_langfuse() -> Check:
    pub = os.getenv("LANGFUSE_PUBLIC_KEY")
    sec = os.getenv("LANGFUSE_SECRET_KEY")
    if not (pub and sec):
        return Check("Langfuse", False, "keys not set (optional for week 1)")
    return Check("Langfuse", True, "keys present")


def main() -> int:
    console.print("\n[bold cyan]ClaimSight environment verification[/bold cyan]\n")

    checks = [
        check_env_var("DATABASE_URL"),
        check_database(),
        check_env_var("GROQ_API_KEY"),
        check_groq(),
        check_env_var("ANTHROPIC_API_KEY"),
        check_anthropic(),
        check_langfuse(),
    ]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Detail")

    for c in checks:
        status = "[green]✓[/green]" if c.passed else "[red]✗[/red]"
        table.add_row(c.name, status, c.detail)

    console.print(table)
    console.print()

    # Langfuse is optional in week 1, don't fail the script if it's missing
    critical_failures = [c for c in checks if not c.passed and c.name != "Langfuse"]
    if critical_failures:
        console.print(f"[red]✗ {len(critical_failures)} critical check(s) failed.[/red]")
        return 1

    console.print("[green]✓ All critical checks passed. You're ready to build.[/green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
