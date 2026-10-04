"""Command line interface (CLI) entrypoint for the RFP Intelligence Platform."""

import json
from pathlib import Path
from typing import Optional
import typer
import uvicorn

from rfp_intelligence.agents.comparison import BidComparisonAgent
from rfp_intelligence.agents.gonogo import GoNoGoAgent
from rfp_intelligence.agents.graph import run_extraction_pipeline, run_qa_pipeline
from rfp_intelligence.config import REPO_ROOT, settings
from rfp_intelligence.models.domain import BidExtractionResult

cli_app = typer.Typer(
    name="rfp-intelligence",
    help="RFP Intelligence Platform CLI: Extract bid data and query bid documents.",
)


@cli_app.command(name="extract")
def extract_bid(
    bid: Path = typer.Option(
        ...,
        "--bid",
        "-b",
        help="Path to bid directory (e.g. ./Assignment-Data-Statements (AI Engineer-Emplay Inc)/Bid1)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for the extracted JSON file (defaults to deliverables/outputs/{bid_id}.json)",
    ),
) -> None:
    """Run multi-agent extraction pipeline on a target bid folder."""
    target_path = bid if bid.is_absolute() else (REPO_ROOT / bid)
    if not target_path.exists():
        typer.secho(f"Error: Bid directory not found at {target_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    bid_id = target_path.name
    typer.secho(f"[*] Initiating multi-agent extraction pipeline for: {bid_id}", fg=typer.colors.CYAN)

    result: BidExtractionResult = run_extraction_pipeline(target_path, bid_id=bid_id)

    # Determine output path
    dest_path = output or (settings.outputs_dir / f"{bid_id}.json")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    typer.secho(f"[+] Successfully extracted {len(result.fields)} fields!", fg=typer.colors.GREEN, bold=True)
    typer.secho(f"[+] Saved structured JSON artifact to: {dest_path}", fg=typer.colors.GREEN)
    typer.echo(f"    Validation: {result.validation.passed} passed, {result.validation.failed} failed, {result.validation.not_found} not found")
    if result.addendum_changes:
        typer.echo(f"    Addendum Changes: {len(result.addendum_changes)} amendments recorded")


@cli_app.command(name="ask")
def ask_question(
    query: str = typer.Argument(..., help="Question to ask over indexed bids"),
    bid_id: Optional[str] = typer.Option(
        None, "--bid-id", help="Optional bid identifier to restrict scope"
    ),
) -> None:
    """Ask a question against the indexed bids and receive a cited response."""
    typer.secho(f"[*] Query: {query}", fg=typer.colors.CYAN)
    if bid_id:
        typer.echo(f"[*] Filter Bid ID: {bid_id}")

    qa_res = run_qa_pipeline(query, bid_id=bid_id)
    typer.secho("\n--- ANSWER ---", fg=typer.colors.GREEN, bold=True)
    typer.echo(qa_res.answer)

    if qa_res.citations:
        typer.secho("\n--- SOURCE CITATIONS ---", fg=typer.colors.YELLOW)
        for c in qa_res.citations:
            page_str = f"Page {c.page}" if c.page else "Page N/A"
            typer.echo(f"- {c.file} ({page_str})")
            if c.snippet:
                typer.echo(f"  Snippet: {c.snippet}")


@cli_app.command(name="compare")
def compare_bids_cmd(
    bid1_json: Path = typer.Option(
        settings.outputs_dir / "Bid1.json", "--bid1", help="Path to Bid1 extracted JSON"
    ),
    bid2_json: Path = typer.Option(
        settings.outputs_dir / "Bid2.json", "--bid2", help="Path to Bid2 extracted JSON"
    ),
    output_report: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Path to save markdown report"
    ),
) -> None:
    """Compare multiple extracted bids side-by-side."""
    typer.secho("[*] Generating side-by-side bid comparison report...", fg=typer.colors.CYAN)
    bids = []
    for p in [bid1_json, bid2_json]:
        path = p if p.is_absolute() else (REPO_ROOT / p)
        if not path.exists():
            typer.secho(f"Error: Extraction file not found: {path}. Run 'extract' first.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        with open(path, "r", encoding="utf-8") as f:
            bids.append(BidExtractionResult(**json.load(f)))

    agent = BidComparisonAgent()
    report = agent.compare_bids(bids)

    out_file = output_report or (REPO_ROOT / "deliverables" / "bid_comparison_report.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report)

    typer.secho(f"[+] Comparison report written to: {out_file}", fg=typer.colors.GREEN)
    typer.echo("\n" + report[:800] + "\n...")


@cli_app.command(name="gonogo")
def gonogo_cmd(
    bid_json: Path = typer.Option(
        ..., "--bid", "-b", help="Path to extracted bid JSON file"
    ),
) -> None:
    """Run automatic Go / No-Go decision recommendation on an extracted bid."""
    target_path = bid_json if bid_json.is_absolute() else (REPO_ROOT / bid_json)
    if not target_path.exists():
        typer.secho(f"Error: File not found: {target_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with open(target_path, "r", encoding="utf-8") as f:
        bid_obj = BidExtractionResult(**json.load(f))

    agent = GoNoGoAgent()
    decision = agent.evaluate(bid_obj)

    color = typer.colors.GREEN if decision.recommendation == "GO" else (
        typer.colors.YELLOW if decision.recommendation == "CAUTION" else typer.colors.RED
    )
    typer.secho(f"\n=== GO / NO-GO RECOMMENDATION: {decision.recommendation} ===", fg=color, bold=True)
    typer.echo(f"Target Bid: {decision.bid_id}")
    typer.echo(f"Capability Alignment Score: {decision.match_score}/100")
    typer.echo(f"Rationale: {decision.rationale}\n")

    typer.secho("Passed Criteria:", fg=typer.colors.GREEN)
    for c in decision.passed_criteria:
        typer.echo(f"  [+] {c}")

    if decision.flagged_risks:
        typer.secho("\nFlagged Risks / Action Items:", fg=typer.colors.YELLOW)
        for r in decision.flagged_risks:
            typer.echo(f"  [!] {r}")


@cli_app.command(name="serve")
def start_server(
    host: str = typer.Option(
        settings.api_host, "--host", "-h", help="Host interface to bind"
    ),
    port: int = typer.Option(
        settings.api_port, "--port", "-p", help="Port to listen on"
    ),
    reload: bool = typer.Option(False, "--reload", help="Enable live auto-reloading"),
) -> None:
    """Start the FastAPI REST server."""
    typer.echo(f"Starting RFP Intelligence REST server at http://{host}:{port}")
    uvicorn.run("rfp_intelligence.api:app", host=host, port=port, reload=reload)


@cli_app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    bid: Optional[Path] = typer.Option(
        None,
        "--bid",
        "-b",
        help="Direct shortcut: extract structured data from specified bid folder",
    ),
) -> None:
    """Default callback when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        if bid is not None:
            extract_bid(bid=bid, output=None)
        else:
            typer.echo(ctx.get_help())
