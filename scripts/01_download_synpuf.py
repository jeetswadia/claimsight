"""Download a SynPUF sample from CMS.

CMS publishes the Medicare Claims Synthetic Public Use Files (SynPUF) — fully
synthetic claims data with no PHI risk. Sample 1 is ~10K beneficiaries which
is plenty for a portfolio project.

Reference: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files

Note: CMS occasionally changes URLs. If the download fails, search
"CMS DE-SynPUF Sample 1" and update SYNPUF_URLS below. Alternatively, the
Synthea synthetic-patient generator (https://github.com/synthetichealth/synthea)
is an excellent fallback that runs entirely locally and produces FHIR-format
synthetic claims.

Usage:
    python scripts/01_download_synpuf.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()

# These URLs may rotate. If they break, the fallback is Synthea — see module docstring.
SYNPUF_URLS = {
    "beneficiary_2008": "https://www.cms.gov/files/zip/de10sample1a.zip",
    "inpatient_2008": "https://www.cms.gov/files/zip/de10sample1b.zip",
    "outpatient_2008": "https://www.cms.gov/files/zip/de10sample1c.zip",
}

OUT_DIR = Path("data/raw/synpuf")


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        console.print(f"[yellow]skip[/yellow] {dest.name} (already exists)")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(dest.name, total=total)
                with open(dest, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=65536):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        return True
    except Exception as e:
        console.print(f"[red]failed[/red] {url}: {e}")
        if dest.exists():
            dest.unlink()
        return False


def main() -> int:
    console.print("\n[bold cyan]Downloading SynPUF Sample 1[/bold cyan]")
    console.print(
        "[dim]If downloads fail, see module docstring for the Synthea fallback.[/dim]\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = []
    for name, url in SYNPUF_URLS.items():
        dest = OUT_DIR / f"{name}.zip"
        if not download(url, dest):
            failures.append(name)

    if failures:
        console.print(f"\n[red]✗ {len(failures)} download(s) failed: {failures}[/red]")
        console.print("[yellow]Consider using Synthea instead — see module docstring.[/yellow]")
        return 1

    console.print(f"\n[green]✓ All files downloaded to {OUT_DIR}/[/green]")
    console.print("[dim]Next: unzip and run scripts/03_load_synpuf.py[/dim]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
