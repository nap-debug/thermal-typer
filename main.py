#!/usr/bin/env python3
"""
main.py
───────
Entry point for Thermal Typer.

Usage
─────
  python main.py           # CLI + web UI (normal SSH use)
  python main.py --no-cli  # web UI only (used by systemd service)
"""

import sys
import logging
import argparse
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
    parser = argparse.ArgumentParser(description="Thermal Typer")
    parser.add_argument(
        "--no-cli",
        action="store_true",
        help="Run web UI only, no CLI (used by systemd service)"
    )
    args = parser.parse_args()

    config = load_config(Path("config.toml"))
    logger.info("Config loaded.")

    from typewriter.printer import Printer
    from typewriter import web

    printer = Printer(config["printer"])
    logger.info("Printer initialised (will connect on first use).")

    # Always start the web UI
    web.run(printer, config["web"])

    if args.no_cli:
        # Service mode — no terminal, just keep the process alive
        logger.info("Running in service mode. Web UI on port %d.", config["web"]["port"])
        logger.info("Press Ctrl-C to stop.")
        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutting down.")
    else:
        # Interactive mode — hand control to the CLI
        from typewriter import cli
        cli_config = {**config["printer"], **config["cli"]}
        cli.run(printer, cli_config)


if __name__ == "__main__":
    main()