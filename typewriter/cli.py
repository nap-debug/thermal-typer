"""
typewriter/cli.py
─────────────────
Terminal (SSH) interface.

Two modes:

  Live mode (default)
    Every keystroke prints immediately — real typewriter feel.
    Backspace removes the character from your screen but prints
    a [BS] marker on paper. Thermal paper can't erase.

  Line mode
    Type a full line, press Enter to print.
    Easier to correct mistakes before committing.

Toggle between modes at runtime:
    /live  — switch to live mode
    /line  — switch to line mode
"""

import logging
import sys
import tty
import termios

from .dispatcher import dispatch, Response

logger = logging.getLogger(__name__)

BANNER = """
╔══════════════════════════════════════╗
║      Thermal Typer  v2.0             ║
║  ─────────────────────────────────   ║
║  type    →  prints                   ║
║  !name   →  shortcut                 ║
║  cut     →  cut paper                ║
║  help    →  list shortcuts           ║
║  exit    →  quit                     ║
║  /live   →  live mode (per key)      ║
║  /line   →  line mode (per Enter)    ║
╚══════════════════════════════════════╝
"""


# ── Raw keypress reader ───────────────────────────────────────────── #

def _getch():
    """Read a single raw character from stdin without waiting for Enter."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


# ── Live mode ─────────────────────────────────────────────────────── #

def _run_live(printer, config: dict):
    """
    Live typewriter mode.

    Each printable keystroke is sent to the printer immediately.
    Enter sends a newline to the printer and checks if the
    accumulated line was a command (exit, /line, etc).
    """
    print("[LIVE MODE] Each keystroke prints immediately.")
    print("Ctrl-C or type 'exit' then Enter to quit.\n")

    buf = []  # accumulates current line for command detection on Enter

    while True:
        ch = _getch()
        code = ord(ch)

        # Ctrl-C or Ctrl-D — exit immediately
        if code in (3, 4):
            print("\nExiting.")
            return "exit"

        # Enter — check if the line was a command
        if ch in ("\r", "\n"):
            line = "".join(buf).strip()
            buf.clear()
            print()  # move terminal cursor down

            if line.lower() == "/line":
                print("[Switching to line mode]")
                return "line"

            if line.lower() in ("exit", "quit"):
                print("Goodbye!")
                return "exit"

            # Send newline to printer
            # (the characters were already printed one by one)
            try:
                printer.print_char("\n")
            except Exception as e:
                print(f"[Printer error: {e}]")
            continue

        # Backspace
        if code in (127, 8):
            if buf:
                buf.pop()
                # Erase character on screen
                sys.stdout.write("\b \b")
                sys.stdout.fl