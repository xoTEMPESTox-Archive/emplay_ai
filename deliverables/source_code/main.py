"""Main entrypoint script for running RFP Intelligence CLI or single-command extraction."""

import sys
from pathlib import Path

# Ensure src/ is in the module search path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from rfp_intelligence.cli import cli_app

app = cli_app

if __name__ == "__main__":
    cli_app()
