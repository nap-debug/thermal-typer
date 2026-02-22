cat > typewriter/cli.py << 'ENDOFFILE'
"""
typewriter/cli.py
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
║  type    ->  prints                  ║
║  !name   ->  shortcut                ║
║  cut     ->  cut paper               ║
║  help    ->  list shortcuts          ║
║  exit    ->  quit                    ║
║  /live   ->  live mode (per key)     ║
║  /line   ->  line mode (per Enter)   ║
╚══════════════════════════════════════╝
"""

def _getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

def _run_live(printer, config: dict):
    print("[LIVE MODE] Each keystroke prints immediately.")
    print("Ctrl-C or type 'exit' then Enter to quit.\n")
    buf = []
    while True:
        ch = _getch()
        code = ord(ch)
        if code in (3, 4):
            print("\nExiting.")
            return "exit"
        if ch in ("\r", "\n"):
            line = "".join(buf).strip()
            buf.clear()
            print()
            if line.lower() == "/line":
                print("[Switching to line mode]")
                return "line"
            if line.lower() in ("exit", "quit"):
                print("Goodbye!")
                return "exit"
            try:
                printer.print_char("\n")
            except Exception as e:
                print(f"[Printer error: {e}]")
            continue
        if code in (127, 8):
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            try:
                printer.print_char("~")
            except Exception:
                pass
            continue
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
        if ch.isprintable():
            buf.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()
            try:
                printer.print_char(ch)
            except Exception as e:
                print(f"\r[Printer error: {e}]")

def _run_line(printer, config: dict):
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
        resp = dispatch(line, printer, config)
        if resp.message == "__EXIT__":
            print("Goodbye!")
            return "exit"
        if resp.message:
            print(f"  {resp.message}")

def run(printer, config: dict):
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
ENDOFFILE