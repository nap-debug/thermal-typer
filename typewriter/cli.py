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
║  ─────────────────────────────────  ║
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
                sys.stdout.flush()
            # Print a marker on paper — thermal can't erase
            try:
                printer.print_char("~")
            except Exception:
                pass
            continue

        # Escape sequences (arrow keys etc) — skip silently
        if code == 27:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdin.read(2)
            except Exception:
                pass
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            continue

        # Printable character — print to screen and printer
        if ch.isprintable():
            buf.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()
            try:
                printer.print_char(ch)
            except Exception as e:
                print(f"\r[Printer error: {e}]")


# ── Line mode ─────────────────────────────────────────────────────── #

def _run_line(printer, config: dict):
    """
    Line mode — type a full line and press Enter to print.
    """
    print("[LINE MODE] Press Enter to print each line.")
    print("Type '/live' to switch to live mode.\n")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return "exit"

        if line.lower() == "/live":
            return "live"

        resp: Response = dispatch(line, printer, config)

        if resp.message == "__EXIT__":
            print("Goodbye!")
            return "exit"

        if resp.message:
            print(f"  {resp.message}")


# ── Entry point ───────────────────────────────────────────────────── #

def run(printer, config: dict):
    """
    Start the CLI loop.
    Reads live_mode from config to decide starting mode.
    """
    print(BANNER)

    mode = "live" if config.get("live_mode", True) else "line"

    while True:
        if mode == "live":
            result = _run_live(printer, config)
        else:
            result = _run_line(printer, config)

        if result == "exit":
            break
        elif result == "live":
            mode = "live"
            print("[Switched to live mode]")
        elif result == "line":
            mode = "line"
            print("[Switched to line mode]")