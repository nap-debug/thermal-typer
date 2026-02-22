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
    
 # Silence Flask's per-request logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    
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

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Thermal Typer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --paper:      #f5f0e8;
    --aged:       #e8e0cc;
    --ink:        #1a1410;
    --faded:      #6b5d4f;
    --ribbon:     #2d1f14;
    --accent:     #4a3728;
    --red:        #8b2222;
    --key-bg:     #d4c9b8;
    --key-shadow: #a8987f;
  }
  html, body {
    min-height: 100vh;
    background: var(--ribbon);
    font-family: 'Special Elite', cursive;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 2rem 1rem 4rem;
  }
  .platen {
    width: 100%;
    max-width: 620px;
    background: var(--paper);
    box-shadow: 0 0 0 1px #c4b89a, 0 8px 32px rgba(0,0,0,0.5);
    border-radius: 2px;
    overflow: hidden;
  }
  .header {
    padding: 1.2rem 2rem 0.8rem;
    border-bottom: 2px solid var(--aged);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  .header h1 {
    font-size: 1.1rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--ink);
  }
  .header .model {
    font-family: 'Courier Prime', monospace;
    font-size: 0.72rem;
    color: var(--faded);
    letter-spacing: 0.1em;
  }
  .status-bar {
    padding: 0.4rem 2rem;
    background: var(--aged);
    border-bottom: 1px solid #c4b89a;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Courier Prime', monospace;
    font-size: 0.72rem;
    color: var(--faded);
  }
  .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #888;
    transition: background 0.3s;
  }
  .dot.online  { background: #4a7c4a; box-shadow: 0 0 4px #4a7c4a; }
  .dot.offline { background: var(--red); }
  .dot.printing { background: #c8922a; animation: pulse 0.6s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .paper {
    padding: 1.5rem 2.5rem;
    min-height: 220px;
    max-height: 340px;
    overflow-y: auto;
    font-family: 'Courier Prime', monospace;
    font-size: 0.95rem;
    line-height: 1.8;
    color: var(--ink);
    background-image: repeating-linear-gradient(
      180deg,
      transparent 0px, transparent 28px,
      rgba(180,160,130,0.15) 28px, rgba(180,160,130,0.15) 29px
    );
    background-size: 100% 29px;
  }
  .log-line { white-space: pre-wrap; word-break: break-word; min-height: 1.8em; }
  .log-line.meta  { color: var(--faded); font-style: italic; font-size: 0.8rem; }
  .log-line.error { color: var(--red); }
  .composer {
    border-top: 2px solid var(--aged);
    padding: 1rem 2rem 1.2rem;
    background: var(--aged);
  }
  .input-row {
    display: flex;
    gap: 0.6rem;
    align-items: flex-end;
  }
  #msg {
    flex: 1;
    background: var(--paper);
    border: 1px solid #b0a088;
    border-radius: 2px;
    padding: 0.55rem 0.8rem;
    font-family: 'Courier Prime', monospace;
    font-size: 0.95rem;
    color: var(--ink);
    resize: none;
    min-height: 2.6rem;
    outline: none;
    transition: border-color 0.2s;
  }
  #msg:focus { border-color: var(--accent); }
  #msg::placeholder { color: var(--faded); opacity: 0.6; }
  .key-btn {
    background: var(--key-bg);
    border: 1px solid #b0a088;
    border-radius: 3px;
    padding: 0.5rem 1.1rem;
    font-family: 'Special Elite', cursive;
    font-size: 0.85rem;
    color: var(--ribbon);
    cursor: pointer;
    box-shadow: 0 3px 0 var(--key-shadow);
    transition: all 0.1s;
    white-space: nowrap;
  }
  .key-btn:hover  { background: #ddd4c2; }
  .key-btn:active { transform: translateY(2px); box-shadow: 0 1px 0 var(--key-shadow); }
  .key-btn.cut    { color: var(--red); }
  .shortcuts {
    padding: 0.6rem 2rem 1rem;
    border-top: 1px solid #c4b89a;
    background: var(--paper);
  }
  .shortcuts summary {
    font-family: 'Courier Prime', monospace;
    font-size: 0.72rem;
    color: var(--faded);
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    user-select: none;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.6rem;
  }
  .chip {
    font-family: 'Courier Prime', monospace;
    font-size: 0.72rem;
    padding: 2px 10px;
    border: 1px solid #c4b89a;
    border-radius: 20px;
    color: var(--faded);
    cursor: pointer;
    background: var(--aged);
    transition: all 0.15s;
  }
  .chip:hover { background: var(--accent); color: var(--paper); border-color: var(--accent); }
  .paper::-webkit-scrollbar { width: 5px; }
  .paper::-webkit-scrollbar-track { background: var(--aged); }
  .paper::-webkit-scrollbar-thumb { background: #b0a088; border-radius: 3px; }
</style>
</head>
<body>
<div class="platen">
  <div class="header">
    <h1>Thermal Typer</h1>
    <span class="model">Epson TM-T88V</span>
  </div>
  <div class="status-bar">
    <span class="dot" id="dot"></span>
    <span id="status-text">Connecting...</span>
  </div>
  <div class="paper" id="paper">
    <div class="log-line meta">— session started —</div>
  </div>
  <div class="composer">
    <div class="input-row">
      <textarea id="msg" rows="1" placeholder="type something..."></textarea>
      <button class="key-btn" onclick="sendLine()">Print</button>
      <button class="key-btn cut" onclick="doCut()">Cut ✂</button>
    </div>
  </div>
  <details class="shortcuts">
    <summary>Shortcuts</summary>
    <div class="chips" id="chips"></div>
  </details>
</div>
<script>
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