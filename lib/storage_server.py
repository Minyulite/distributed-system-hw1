"""A tiny storage service for Part A. Runs in the `storage` container on port 8000.
It holds one shared counter for scripts/counter_test.py.

Endpoints (JSON in, JSON out):
  GET  /counter                -> {"value": n}
  PUT  /counter  {"value": n}  -> {"ok": true}   (no locking here: read-modify-write races are possible)
  POST /reset                  -> {"ok": true}   (counter = 0)
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

state = {"counter": 0}
mutex = threading.Lock()  # protects `state` inside this server only


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path == "/counter":
            with mutex:
                return self._send(200, {"value": state["counter"]})
        self._send(404, {"error": "not found"})

    def do_PUT(self):
        if self.path == "/counter":
            v = self._body()["value"]
            time.sleep(0.002)  # a little service time, so races are visible
            with mutex:
                state["counter"] = v
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/reset":
            with mutex:
                state["counter"] = 0
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})

    def log_message(self, *args):  # keep the container log readable
        pass


if __name__ == "__main__":
    print("storage server on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
