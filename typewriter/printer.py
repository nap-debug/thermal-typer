"""
typewriter/printer.py
─────────────────────
Low-level printer interface.

Owns the USB connection to the Epson TM-T88V.
All other modules talk to this one — nothing else
imports escpos directly.

Key design decisions:
  - Lazy connection: nothing crashes at import time
    if the printer is off or disconnected.
  - Auto-reconnect: if the printer disappears mid-session,
    the next print call retries automatically.
  - Thread-safe: web and CLI can print simultaneously
    without corrupting each other.
"""

import logging
import textwrap
import time
from threading import Lock

logger = logging.getLogger(__name__)


class PrinterError(Exception):
    """Raised when the printer is unreachable after retrying."""


class Printer:
    """
    Thread-safe wrapper around python-escpos.

    Usage:
        p = Printer(config)
        p.print_text("Hello world")
        p.cut()
    """

    def __init__(self, config: dict):
        self._cfg = config
        self._dev = None      # escpos USB instance, None until first use
        self._lock = Lock()   # one print at a time

    # ──────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────

    def print_text(self, text: str, raw: bool = False) -> None:
        """
        Send text to the printer.

        raw=False (default): word-wrapped to chars_per_line.
        raw=True: sent as-is, preserving spacing. Use for ASCII art.
        """
        with self._lock:
            dev = self._get_connection()
            self._set_left_margin(dev)

            if raw:
                dev.text(text if text.endswith("\n") else text + "\n")
                return

            if text.strip() == "":
                dev.text("\n")
                return

            width = self._cfg.get("chars_per_line", 37)
            for para in text.splitlines():
                if not para.strip():
                    dev.text("\n")
                    continue
                for line in textwrap.wrap(
                    para,
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                ):
                    dev.text(line + "\n")

    def print_char(self, char: str) -> None:
        """
        Print a single character immediately.
        Used by live (typewriter) mode in the CLI and web UI.
        """
        with self._lock:
            dev = self._get_connection()
            if char == "\n":
                dev.text("\n")
            elif char.isprintable():
                dev.text(char)

    def cut(self, lines: int = None) -> None:
        """Feed blank lines then cut the paper."""
        if lines is None:
            lines = self._cfg.get("bottom_margin_lines", 4)
        with self._lock:
            dev = self._get_connection()
            dev.text("\n" * lines)
            dev.cut()

    def is_connected(self) -> bool:
        """True if we currently have a live USB handle."""
        return self._dev is not None

    # ──────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────

    def _get_connection(self):
        """
        Return a live escpos device, reconnecting if needed.
        Must be called with self._lock already held.
        """
        if self._dev is not None:
            return self._dev

        interval = self._cfg.get("reconnect_interval", 3)
        attempts = 0

        while True:
            try:
                from escpos.printer import Usb
                dev = Usb(
                    self._cfg["vendor_id"],
                    self._cfg["product_id"],
                )
                self._dev = dev
                logger.info("Printer connected after %d attempt(s).", attempts + 1)
                return dev
            except Exception as exc:
                attempts += 1
                logger.warning(
                    "Printer not reachable (attempt %d): %s — retrying in %ds.",
                    attempts,
                    exc,
                    interval,
                )
                time.sleep(interval)

    def _set_left_margin(self, dev) -> None:
        """Send ESC/POS GS L command to set the hardware left margin."""
        units = self._cfg.get("margin_units", 60)
        nL = units % 256
        nH = units // 256
        dev._raw(b"\x1d\x4c" + bytes([nL, nH]))

    def mark_disconnected(self) -> None:
        """
        Call this if you catch a USB error outside this class.
        Forces a reconnect on the next print attempt.
        """
        self._dev = None