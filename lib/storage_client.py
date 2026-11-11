"""Client helpers for the storage service (Part A)."""
import json
import urllib.request

from lib.zkutil import STORAGE_URL


def _call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(STORAGE_URL + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def get_counter():
    return _call("GET", "/counter")["value"]


def put_counter(v):
    _call("PUT", "/counter", {"value": v})


def reset():
    _call("POST", "/reset")
