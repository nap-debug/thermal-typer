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

    from typewriter.printer import Printer
    from typewriter.dispatcher import dispatch

    print("Connecting to printer...")
    printer = Printer(config["printer"])

    print("Testing dispatcher...")
    tests = [
        "Hello from the dispatcher",
        "!test",
        "!time",
        "!cat",
        "cut",
    ]

    for t in tests:
        print(f"  sending: {repr(t)}")
        resp = dispatch(t, printer, config["printer"])
        print(f"  response: {resp}")


if __name__ == "__main__":
    main()