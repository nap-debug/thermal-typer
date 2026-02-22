"""
typewriter/dispatcher.py
────────────────────────
Central command parser shared by every interface.

CLI, web, and WhatsApp all call dispatch() and get
back a Response. None of them need to know about
shortcuts, commands, or ESC/POS — that all lives here.

Response fields
───────────────
  .printed  bool  — True if something went to the printer
  .message  str   — feedback to show the user
  .error    bool  — True if something went wrong
"""

from __future__ import annotations
from dataclasses import dataclass

from .shortcuts import resolve, list_shortcuts


@dataclass
class Response:
    printed: bool = False
    message: str = ""
    error:   bool = False

    @classmethod
    def ok(cls, msg: str = "", printed: bool = True) -> "Response":
        return cls(printed=printed, message=msg)

    @classmethod
    def err(cls, msg: str) -> "Response":
        return cls(printed=False, message=msg, error=True)


def dispatch(text: str, printer, config: dict) -> Response:
    """
    Parse text and act on it.

    Parameters
    ----------
    text    : raw input string from any interface
    printer : Printer instance
    config  : the [printer] section of config.toml

    Returns
    -------
    Response
    """
    raw   = text.strip()
    lower = raw.lower()

    # ── Empty input ──────────────────────────────────────── #
    if not raw:
        try:
            printer.print_text("")
        except Exception as e:
            return Response.err(f"Printer error: {e}")
        return Response.ok("(blank line printed)")

    # ── Built-in commands ────────────────────────────────── #
    if lower == "cut":
        try:
            printer.cut(config.get("bottom_margin_lines", 4))
        except Exception as e:
            return Response.err(f"Printer error: {e}")
        return Response.ok("Paper cut.")

    if lower in ("exit", "quit"):
        return Response(printed=False, message="__EXIT__")

    if lower in ("help", "shortcuts"):
        names = list_shortcuts()
        lines = ["Available shortcuts:"]
        lines += [f"  !{n}" for n in names]
        lines += ["", "Commands: cut, exit, help"]
        return Response.ok("\n".join(lines), printed=False)

    # ── Shortcut lookup ──────────────────────────────────── #
    result = resolve(lower)
    if result is not None:
        text_to_print, opts = result
        try:
            printer.print_text(text_to_print, **opts)
        except Exception as e:
            return Response.err(f"Printer error: {e}")
        return Response.ok(f"Shortcut '{lower.lstrip('!')}' printed.")

    # ── Plain text ───────────────────────────────────────── #
    try:
        printer.print_text(raw)
    except Exception as e:
        return Response.err(f"Printer error: {e}")

    return Response.ok("Printed.")