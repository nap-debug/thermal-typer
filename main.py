#!/usr/bin/env python3
"""
main.py
───────
Entry point for Thermal Typer.

Currently starts:
  - Printer connection (lazy)
  - CLI interface

Web and WhatsApp interfaces will be added here
as they are built.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(path: Path) -> dict:
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("ERROR: TOML library missing. Run: pip install tomli")
            sys.exit(1)

    if not path.exists():
        print(f"ERROR: config file not found at {path}")
        sys.exit(1)

    with open(path, "rb") as f:
        return tomllib.load(f)


def main():
    config = load_config(Path("config.toml"))
    logger.info("Config loaded.")

    from typewriter.printer import Printer
    from typewriter import cli, web

    printer = Printer(config["printer"])
    logger.info("Printer initialised (will connect on first use).")

    # Start web UI in background thread
    web.run(printer, config["web"])

    # CLI takes over the main thread
    cli_config = {**config["printer"], **config["cli"]}
    cli.run(printer, cli_config)


if __name__ == "__main__":
    main()