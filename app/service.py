import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
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


class Handler(BaseHTTPRequestHandler):
    server_version = "blue-green-demo/1.0"

    def do_GET(self):
        if self.path.endswith("/health") or self.path == "/health":
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
