"""
typewriter/shortcuts.py
───────────────────────
Shortcut registry.

A shortcut maps a keyword to something to print.
Three kinds:

  1. Plain string
         "quote": "Something worth printing."
         Printed with word-wrap.

  2. Tuple (string, options)
         "cat": (ascii_art, {"raw": True})
         raw=True preserves spacing — use for ASCII art.

  3. Callable
         "time": lambda: f"Time: {datetime.now()...}"
         Called at print time — use for dynamic content.

Adding a shortcut
─────────────────
Add an entry to SHORTCUTS below. That's it.
Every interface (CLI, web, WhatsApp) shares this
registry automatically via the dispatcher.

Triggering a shortcut
─────────────────────
Type the keyword with or without a leading "!".
Both "time" and "!time" work from any interface.
"""

from datetime import datetime


# ── Dynamic helpers ───────────────────────────────────────────────── #

def _time() -> str:
    return f"Time: {datetime.now().strftime('%H:%M:%S')}"


def _date() -> str:
    return f"Date: {datetime.now().strftime('%A, %B %-d %Y')}"


def _datetime() -> str:
    return datetime.now().strftime("%A, %B %-d %Y  %H:%M:%S")


# ── Registry ──────────────────────────────────────────────────────── #

SHORTCUTS: dict = {

    # ── Dynamic ──────────────────────────────────────────── #
    "time":  _time,
    "date":  _date,
    "now":   _datetime,

    # ── Utility ──────────────────────────────────────────── #
    "test":  ">>> This is a test message <<<",
    "wifi":  "WiFi: my-network\nPass: super-secret",

    # ── Quotes ───────────────────────────────────────────── #
    "focus": (
        "Salvation must grow out of understanding; "
        "total understanding can follow only from total "
        "experience, and experience must be won by the "
        "laborious discipline of shaping one's absolute attention."
    ),

    # ── ASCII art ─────────────────────────────────────────── #
    "cat": (
        r"""
 /\_/\
( o.o )
 > ^ 
""",
        {"raw": True},
    ),

    "robot": (
        r"""
 [o_o]
 /|_|\
  / \
""",
        {"raw": True},
    ),

    "coffee": (
        r"""
 ( (
  ) )
........
|      |]
\      /
 `----'
""",
        {"raw": True},
    ),

    "heart": (
        r"""
  ****  ****
 ****** ******
 *************
  ***********
   *********
    *******
     *****
      ***
       *
""",
        {"raw": True},
    ),
}


# ── Resolver ──────────────────────────────────────────────────────── #

def resolve(keyword: str):
    """
    Look up a keyword in SHORTCUTS.

    Strips leading "!" and lowercases before matching,
    so "!Time", "time", and "!TIME" all resolve the same.

    Returns
    ───────
    (text: str, opts: dict)   if found
    None                      if not found
    """
    key = keyword.lstrip("!").strip().lower()
    entry = SHORTCUTS.get(key)

    if entry is None:
        return None

    # Resolve callables — dynamic shortcuts run here
    if callable(entry):
        entry = entry()

    # Normalise to (text, opts)
    if isinstance(entry, tuple):
        text, opts = entry
    else:
        text, opts = entry, {}

    return text, opts


def list_shortcuts() -> list:
    """Return a sorted list of all shortcut keywords."""
    return sorted(SHORTCUTS.keys())