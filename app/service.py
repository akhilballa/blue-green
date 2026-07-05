import html
import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from string import Template
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
SERVICE_COLOR = os.getenv("SERVICE_COLOR", "blue")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8080"))
DOWNSTREAMS = [
    item.strip()
    for item in os.getenv("DOWNSTREAMS", "").split(",")
    if item.strip()
]

# All five services in the demo, used to build the navigation bar. Links are
# relative, so they resolve through the Nginx gateway (http://localhost:8080).
ALL_SERVICES = ["catalog", "cart", "checkout", "payment", "user"]

START_TIME = time.time()
_request_lock = threading.Lock()
_request_count = 0


def next_request_count():
    global _request_count
    with _request_lock:
        _request_count += 1
        return _request_count


def format_uptime(seconds):
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append("%dd" % days)
    if hours:
        parts.append("%dh" % hours)
    if minutes:
        parts.append("%dm" % minutes)
    parts.append("%ds" % secs)
    return " ".join(parts)


def downstream_health():
    checks = []
    for url in DOWNSTREAMS:
        start = time.perf_counter()
        try:
            with urlopen(url, timeout=0.7) as response:
                body = response.read(4096)
                checks.append(
                    {
                        "url": url,
                        "ok": 200 <= response.status < 300,
                        "status": response.status,
                        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                        "bytes": len(body),
                    }
                )
        except (OSError, URLError, TimeoutError) as exc:
            checks.append(
                {
                    "url": url,
                    "ok": False,
                    "error": exc.__class__.__name__,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                }
            )
    return checks


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

THEMES = {
    "blue": {"accent": "#2563eb", "accent_dark": "#1e40af", "soft": "#dbeafe"},
    "green": {"accent": "#16a34a", "accent_dark": "#15803d", "soft": "#dcfce7"},
}

PAGE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
  :root {
    --accent: $accent;
    --accent-dark: $accent_dark;
    --soft: $soft;
    --bg: #f5f6f8;
    --card: #ffffff;
    --text: #1f2933;
    --muted: #6b7280;
    --border: #e5e7eb;
    --ok: #16a34a;
    --bad: #dc2626;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1216;
      --card: #181c22;
      --text: #e6e8eb;
      --muted: #9aa4b2;
      --border: #2a2f37;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }
  .wrap { max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }
  .bar { height: 6px; border-radius: 6px; background: var(--accent); margin-bottom: 22px; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 26px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  .title-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  h1 { font-size: 1.6rem; margin: 0; text-transform: capitalize; }
  .sub { color: var(--muted); margin: 4px 0 0; font-size: 0.9rem; }
  .color-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--accent); color: #fff;
    padding: 5px 12px; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .color-badge::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #fff; }
  .status {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 14px; border-radius: 999px;
    font-weight: 600; font-size: 0.92rem;
  }
  .status.ok { background: rgba(22,163,74,0.12); color: var(--ok); }
  .status.bad { background: rgba(220,38,38,0.12); color: var(--bad); }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; }
  .status.ok .dot { animation: pulse 1.8s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
  .grid {
    margin-top: 24px;
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
  }
  @media (max-width: 520px) { .grid { grid-template-columns: 1fr; } }
  .cell {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 14px;
  }
  .cell .k { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }
  .cell .v { font-size: 1.02rem; font-weight: 600; margin-top: 3px; word-break: break-word; }
  h2 { font-size: 1.05rem; margin: 28px 0 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); }
  th { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }
  td.url { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; word-break: break-all; }
  .pill { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
  .pill.ok { background: rgba(22,163,74,0.12); color: var(--ok); }
  .pill.bad { background: rgba(220,38,38,0.12); color: var(--bad); }
  .muted { color: var(--muted); font-size: 0.9rem; }
  nav { margin-top: 30px; display: flex; flex-wrap: wrap; gap: 8px; }
  nav a {
    text-decoration: none; color: var(--text);
    border: 1px solid var(--border); background: var(--card);
    padding: 7px 13px; border-radius: 999px; font-size: 0.86rem;
    text-transform: capitalize; transition: all 0.15s;
  }
  nav a:hover { border-color: var(--accent); color: var(--accent); }
  nav a.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  footer { margin-top: 26px; text-align: center; color: var(--muted); font-size: 0.8rem; }
  footer code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="bar"></div>
    <div class="card">
      <div class="head">
        <div>
          <div class="title-row">
            <h1>$service</h1>
            <span class="color-badge">$color_label</span>
          </div>
          <p class="sub">$subtitle</p>
        </div>
        <span class="status $status_class"><span class="dot"></span>$status_label</span>
      </div>

      <div class="grid">
        <div class="cell"><div class="k">Version</div><div class="v">$version</div></div>
        <div class="cell"><div class="k">Active colour</div><div class="v">$color_label</div></div>
        <div class="cell"><div class="k">Hostname</div><div class="v">$hostname</div></div>
        <div class="cell"><div class="k">Uptime</div><div class="v">$uptime</div></div>
        <div class="cell"><div class="k">Requests served</div><div class="v">$requests</div></div>
        <div class="cell"><div class="k">Server time (UTC)</div><div class="v">$timestamp</div></div>
      </div>

      $extra

      <nav>$nav</nav>
    </div>
    <footer>
      Zero-Downtime Blue-Green Deployment Demo &middot;
      request path <code>$path</code> &middot;
      <a href="?format=json" style="color:inherit">view raw JSON</a>
    </footer>
  </div>
</body>
</html>
"""
)


def _nav_html():
    items = []
    for name in ALL_SERVICES:
        cls = "active" if name == SERVICE_NAME else ""
        items.append(
            '<a class="%s" href="/api/%s">%s</a>' % (cls, name, html.escape(name))
        )
    items.append('<a href="/health">gateway&nbsp;health</a>')
    return "".join(items)


def _downstream_html(downstreams):
    if not DOWNSTREAMS:
        return (
            '<h2>Downstream dependencies</h2>'
            '<p class="muted">This service has no downstream dependencies &mdash; '
            "it is a leaf service.</p>"
        )
    rows = []
    for item in downstreams:
        ok = item.get("ok")
        pill = (
            '<span class="pill ok">healthy</span>'
            if ok
            else '<span class="pill bad">unreachable</span>'
        )
        detail = item.get("status", item.get("error", "-"))
        rows.append(
            "<tr><td class=\"url\">%s</td><td>%s</td><td>%s</td><td>%s ms</td></tr>"
            % (
                html.escape(item.get("url", "")),
                pill,
                html.escape(str(detail)),
                html.escape(str(item.get("latency_ms", "-"))),
            )
        )
    return (
        "<h2>Downstream dependencies</h2>"
        "<table><thead><tr><th>Endpoint</th><th>Status</th>"
        "<th>Detail</th><th>Latency</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_page(kind, status_ok, path, downstreams=None):
    theme = THEMES.get(SERVICE_COLOR, THEMES["blue"])
    if kind == "health":
        subtitle = "Liveness check &mdash; the service process is responding to requests."
        extra = (
            '<h2>Health check</h2>'
            '<p class="muted">This endpoint reports whether the <strong>%s</strong> '
            "service process is alive. Container, gateway, and deployment health checks "
            "poll this route before traffic is switched between colours.</p>"
            % html.escape(SERVICE_NAME)
        )
    else:
        subtitle = "Blue-Green deployment demo service"
        extra = _downstream_html(downstreams or [])

    values = {
        "title": "%s (%s) - %s" % (SERVICE_NAME, SERVICE_COLOR, SERVICE_VERSION),
        "accent": theme["accent"],
        "accent_dark": theme["accent_dark"],
        "soft": theme["soft"],
        "service": html.escape(SERVICE_NAME),
        "subtitle": subtitle,
        "color_label": html.escape(SERVICE_COLOR),
        "status_class": "ok" if status_ok else "bad",
        "status_label": "Healthy" if status_ok else "Degraded",
        "version": html.escape(SERVICE_VERSION),
        "hostname": html.escape(socket.gethostname()),
        "uptime": format_uptime(time.time() - START_TIME),
        "requests": str(next_request_count()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "path": html.escape(path),
        "extra": extra,
        "nav": _nav_html(),
    }
    return PAGE.substitute(values)


class Handler(BaseHTTPRequestHandler):
    server_version = "blue-green-demo/1.0"

    def _use_html(self, query):
        # A browser sends "Accept: text/html"; tooling (curl, healthchecks,
        # wrk, Ansible) does not, so it keeps getting JSON. `?format=json`
        # lets a browser opt back into the raw JSON on demand.
        if "format=json" in query:
            return False
        return "text/html" in self.headers.get("Accept", "")

    def do_GET(self):
        route = urlsplit(self.path)
        path, query = route.path, route.query

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        is_health = path.endswith("/health") or path == "/health"

        if is_health:
            if self._use_html(query):
                self._send_html(render_page("health", True, self.path))
            else:
                self._send_json(
                    {
                        "status": "ok",
                        "service": SERVICE_NAME,
                        "color": SERVICE_COLOR,
                        "version": SERVICE_VERSION,
                        "hostname": socket.gethostname(),
                    }
                )
            return

        downstreams = downstream_health()
        all_downstreams_ok = all(item["ok"] for item in downstreams)
        status_code = 200 if all_downstreams_ok else 503

        if self._use_html(query):
            self._send_html(
                render_page("service", all_downstreams_ok, self.path, downstreams),
                status_code=status_code,
            )
        else:
            self._send_json(
                {
                    "service": SERVICE_NAME,
                    "color": SERVICE_COLOR,
                    "version": SERVICE_VERSION,
                    "hostname": socket.gethostname(),
                    "path": self.path,
                    "timestamp": time.time(),
                    "downstreams": downstreams,
                },
                status_code=status_code,
            )

    def log_message(self, fmt, *args):
        print(
            json.dumps(
                {
                    "service": SERVICE_NAME,
                    "color": SERVICE_COLOR,
                    "client": self.client_address[0],
                    "message": fmt % args,
                }
            ),
            flush=True,
        )

    def _send_json(self, payload, status_code=200):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, markup, status_code=200):
        body = markup.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", SERVICE_PORT), Handler)
    print(
        json.dumps(
            {
                "event": "service_started",
                "service": SERVICE_NAME,
                "color": SERVICE_COLOR,
                "version": SERVICE_VERSION,
                "port": SERVICE_PORT,
                "downstreams": DOWNSTREAMS,
            }
        ),
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
