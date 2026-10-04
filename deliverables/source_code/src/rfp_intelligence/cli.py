"""Command line interface (CLI) entrypoint for the RFP Intelligence Platform."""

from pathlib import Path
from typing import Optional
import typer
import uvicorn
from rfp_intelligence.config import settings

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
    typer.echo(f"Initiating extraction for bid directory: {bid}")
    typer.echo(
        "[TODO: Pipeline not yet implemented - will run multi-agent extraction in Phase 3/4]"
    )


@cli_app.command(name="ask")
def ask_question(
    query: str = typer.Argument(..., help="Question to ask over indexed bids"),
    bid_id: Optional[str] = typer.Option(
        None, "--bid-id", help="Optional bid identifier to restrict scope"
    ),
) -> None:
    """Ask a question against the indexed bids and receive a cited response."""
    typer.echo(f"Query: {query}")
    if bid_id:
        typer.echo(f"Filter Bid ID: {bid_id}")
    typer.echo(
        "[TODO: Q&A agent not yet implemented - will run retrieval and citation synthesis in Phase 3]"
    )


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
