#!/usr/bin/env python3
"""
main.py
-------
Entry point. Currently just loads and validates config.
We'll add more here as each module is built.
"""

import sys
from pathlib import Path


def load_config(path: Path) -> dict:
    try:
        import tomllib          # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib   # backport
        except ImportError:
            print("ERROR: TOML library missing.")
            print("Run: pip install tomli")
            sys.exit(1)

    if not path.exists():
        print(f"ERROR: config file not found at {path}")
        sys.exit(1)

    with open(path, "rb") as f:
        return tomllib.load(f)


def main():
    config = load_config(Path("config.toml"))
    print("Config loaded successfully.")
    print(f"  Printer:  {hex(config['printer']['vendor_id'])}:{hex(config['printer']['product_id'])}")
    print(f"  Web port: {config['web']['port']}")
    print(f"  Live mode: {config['cli']['live_mode']}")


if __name__ == "__main__":
    main()