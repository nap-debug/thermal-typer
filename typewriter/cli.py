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
    Live mode — auto-prints when the line fills up.
    No Enter needed. Silent on success.
    Commands are detected when you press Enter on a command word.
    """
    print("[LIVE MODE] Prints automatically as you type.")
    print("Press Enter after a command (exit, cut, !shortcut, /line).\n")

    width = config.get("chars_per_line", 37)
    buf = []

    while True:
        ch = _getch()
        code = ord(ch)

        # Ctrl-C or Ctrl-D
        if code in (3, 4):
            print("\nExiting.")
            return "exit"

        # Enter — only used for commands
        if ch in ("\r", "\n"):
            line = "".join(buf).strip()
            buf.clear()
            print()

            if not line:
                try:
                    printer.print_char("\n")
                except Exception as e:
                    print(f"[Printer error: {e}]")
                continue

            if line.lower() == "/line":
                print("[Switching to line mode]")
                return "line"

            resp = dispatch(line, printer, config)

            if resp.message == "__EXIT__":
                print("Goodbye!")
                return "exit"

            if resp.error:
                print(f"  {resp.message}")
            continue

        # Backspace — fix screen only, no printer marker
        if code in (127, 8):
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue

        # Escape sequences (arrow keys etc) — skip
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

        # Printable character
        if ch.isprintable():
            buf.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()

            # Auto-print when buffer hits line width
            if len(buf) >= width:
                line = "".join(buf)

                # Break at the last space for word wrapping
                last_space = line.rfind(" ")
                if last_space > 0:
                    to_print = line[:last_space]
                    leftover = line[last_space + 1:]
                else:
                    to_print = line
                    leftover = ""

                buf = list(leftover)
                print()  # just move cursor to next line, no rewriting

                try:
                    printer.print_text(to_print)
                except Exception as e:
                    print(f"[Printer error: {e}]")


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

        if resp.error:
            print(f"  {resp.message}")
        elif resp.message and not resp.printed:
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