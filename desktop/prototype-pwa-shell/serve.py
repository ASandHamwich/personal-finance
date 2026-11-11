"""PROTOTYPE — throwaway. Stand-in "server" for trying Mac app shapes.

Run:  python3 desktop/prototype-pwa-shell/serve.py
Then open http://localhost:3999 . Ctrl-C to simulate the server being down.
"""
import http.server
import json
import pathlib
import socketserver
import time

HERE = pathlib.Path(__file__).parent
PUBLIC = HERE.parent.parent / "public"
PORT = 3999
STARTED = time.strftime("%H:%M:%S")

ROUTES = {
    "/": ("index.html", "text/html"),
    "/transactions": ("index.html", "text/html"),
    "/accounts": ("index.html", "text/html"),
    "/manifest.json": ("manifest.json", "application/manifest+json"),
    "/service-worker.js": ("service-worker.js", "text/javascript"),
    "/offline.html": ("offline.html", "text/html"),
}
PUBLIC_FILES = {"/logo-pwa.png", "/logo-pwa-maskable.png", "/android-chrome-192x192.png", "/logo-offline.svg"}


class Handler(http.server.BaseHTTPRequestHandler):
    def send(self, body, ctype, status=200, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/up":
            return self.send(json.dumps({"ok": True, "started": STARTED}).encode(), "application/json")
        if path == "/export.csv":
            csv = b"date,name,amount\n2026-11-01,Hawker centre,-6.50\n2026-11-02,Salary,5200.00\n"
            return self.send(csv, "text/csv", extra={"Content-Disposition": 'attachment; filename="prototype-export.csv"'})
        if path in ROUTES:
            name, ctype = ROUTES[path]
            return self.send((HERE / name).read_bytes(), ctype)
        if path in PUBLIC_FILES:
            ctype = "image/svg+xml" if path.endswith(".svg") else "image/png"
            return self.send((PUBLIC / path.lstrip("/")).read_bytes(), ctype)
        self.send(b"not found", "text/plain", 404)

    def log_message(self, fmt, *args):
        print(f"[prototype] {self.command} {self.path}")


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"PROTOTYPE shell server on http://localhost:{PORT}  (started {STARTED}) — Ctrl-C to 'take the server down'")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[prototype] server down")
