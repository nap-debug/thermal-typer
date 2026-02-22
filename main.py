#!/usr/bin/env python3
"""
main.py
-------
Entry point. Currently loads config and runs a printer test.
"""

import sys
from pathlib import Path


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
    print("Config loaded successfully.")

    # ── Printer test ────────────────────────────────── #
    from typewriter.printer import Printer

    print("Connecting to printer...")
    printer = Printer(config["printer"])

    print("Sending test print...")
    printer.print_text("Thermal Typer v2")
    printer.print_text("Config loaded successfully.")
    printer.print_text(f"chars_per_line: {config['printer']['chars_per_line']}")
    printer.print_text("If you can read this, the printer is working.")
    printer.cut()

    print("Done. Check the printer!")


if __name__ == "__main__":
    main()