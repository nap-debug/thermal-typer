"""
typewriter/web.py
─────────────────
Local web interface.

Serves a single-page typewriter UI on port 5000.
Runs in a background thread alongside the CLI.

Routes
──────
  GET  /          → serves the UI
  POST /print     → receives text, calls dispatch()
  GET  /status    → printer connection status
  GET  /shortcuts → list of available shortcuts
"""

import logging
import threading

from flask import Flask, jsonify, render_template_string, request

from .dispatcher import dispatch

logger = logging.getLogger(__name__)


def create_app(printer, config: dict):
    from .shortcuts import list_shortcuts

    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(HTML)

    @app.route("/status")
    def status():
        return jsonify(connected=printer.is_connected())

    @app.route("/shortcuts")
    def shortcuts():
        return jsonify(shortcuts=list_shortcuts())

    @app.route("/print", methods=["POST"])
    def print_line():
        data = request.get_json(force=True)
        text = data.get("text", "")
        resp = dispatch(text, printer, config)
        return jsonify(
            printed=resp.printed,
            message=resp.message,
            error=resp.error
        )

    @app.route("/char", methods=["POST"])
    def print_char():
        data = request.get_json(force=True)
        ch = data.get("char", "")
        if ch:
            try:
                printer.print_char(ch)
            except Exception as e:
                return jsonify(error=True, message=str(e))
        return jsonify(ok=True)

    return app


def run(printer, config: dict):
    """Start Flask in a daemon thread."""
    app = create_app(printer, config)
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 5000)
    logger.info("Web UI starting on http://%s:%d", host, port)
    t = threading.Thread(
        target=lambda: app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        ),
        daemon=True,
        name="web-server",
    )
    t.start()
    return t

HTML += """<script>
const paper = document.getElementById('paper');
const msgEl = document.getElementById('msg');

function appendLog(text, cls) {
  const el = document.createElement('div');
  el.className = 'log-line' + (cls ? ' ' + cls : '');
  el.textContent = text;
  paper.appendChild(el);
  paper.scrollTop = paper.scrollHeight;
}

async function pollStatus() {
  try {
    const r = await fetch('/status');
    const d = await r.json();
    const dot = document.getElementById('dot');
    const txt = document.getElementById('status-text');
    dot.className = 'dot ' + (d.connected ? 'online' : 'offline');
    txt.textContent = d.connected ? 'Printer online' : 'Printer offline';
  } catch(e) {}
}
setInterval(pollStatus, 4000);
pollStatus();

async function loadShortcuts() {
  try {
    const r = await fetch('/shortcuts');
    const d = await r.json();
    const chips = document.getElementById('chips');
    chips.innerHTML = '';
    d.shortcuts.forEach(s => {
      const c = document.createElement('span');
      c.className = 'chip';
      c.textContent = '!' + s;
      c.onclick = () => send('!' + s);
      chips.appendChild(c);
    });
  } catch(e) {}
}
loadShortcuts();

async function send(text) {
  if (!text.trim()) return;
  document.getElementById('dot').className = 'dot printing';
  try {
    const r = await fetch('/print', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const d = await r.json();
    if (d.error) {
      appendLog('error: ' + d.message, 'error');
    } else if (d.message && !d.printed) {
      appendLog(d.message, 'meta');
    } else {
      appendLog(text);
    }
  } catch(e) {
    appendLog('network error', 'error');
  }
  setTimeout(pollStatus, 500);
}

async function sendLine() {
  const text = msgEl.value.trim();
  if (!text) return;
  msgEl.value = '';
  await send(text);
  msgEl.focus();
}

async function doCut() {
  appendLog('— cut —', 'meta');
  await send('cut');
}

msgEl.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    await sendLine();
  }
});
</script>
</body>
</html>"""