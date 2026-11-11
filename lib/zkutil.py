"""Shared helpers for the ZooKeeper homework. You may use these freely.

Server names are zk1, zk2, ... . Inside the dev container they resolve to the servers'
client addresses. (ZK_MAP lets the same code run elsewhere, e.g.
ZK_MAP="zk1=127.0.0.1:2181,zk2=127.0.0.1:2182,zk3=127.0.0.1:2183".)
"""
import logging
import os
import socket
import time

from kazoo.client import KazooClient

logging.basicConfig(level=logging.ERROR)  # hide Kazoo's reconnect chatter; set to INFO to see it

N_SERVERS = int(os.environ.get("ZK_SERVERS", "3"))
SERVERS = [f"zk{i}" for i in range(1, N_SERVERS + 1)]
_MAP = dict(kv.split("=") for kv in os.environ.get("ZK_MAP", "").split(",") if kv)
STORAGE_URL = os.environ.get("STORAGE_URL", "http://storage:8000")


def addr(name):
    """'zk2' -> 'zk2:2181' (or the ZK_MAP override)."""
    return _MAP.get(name, f"{name}:2181")


def hosts(*names):
    """Connection string for the given servers; all servers if none given."""
    return ",".join(addr(n) for n in (names or SERVERS))


def connect(*names, timeout=10.0, read_only=False, randomize=True):
    """Start a KazooClient connected to one of `names` (default: any server).

    timeout   : requested session timeout in seconds (ZooKeeper clamps it to 4–40 s
                with the tickTime used in this homework)
    read_only : allow connecting to a server that is in read-only mode
    randomize : False = try the servers in the order given
    """
    zk = KazooClient(hosts=hosts(*names), timeout=timeout, read_only=read_only,
                     randomize_hosts=randomize, connection_retry={"max_tries": -1, "max_delay": 1})
    zk.start(timeout=30)
    return zk


def connected_server(zk):
    """Name of the server this client is currently connected to, e.g. 'zk2'."""
    host, port = zk._connection._socket.getpeername()[:2]
    for n in SERVERS:
        h, p = addr(n).split(":")
        try:
            if socket.gethostbyname(h) == host and int(p) == port:
                return n
        except OSError:
            pass
    return f"{host}:{port}"


def four_letter(name, cmd="srvr", timeout=2.0):
    """Send a four-letter command (srvr, stat, ruok, mntr) to a server; return the reply text."""
    h, p = addr(name).split(":")
    try:
        with socket.create_connection((h, int(p)), timeout=timeout) as s:
            s.sendall(cmd.encode())
            chunks = []
            while True:
                b = s.recv(4096)
                if not b:
                    break
                chunks.append(b)
        return b"".join(chunks).decode(errors="replace")
    except OSError as e:
        return f"unreachable ({e.__class__.__name__})"


def server_state(name):
    """(mode, zxid) of a server from 'srvr'. mode is leader/follower/read-only/... or None."""
    mode, zxid = None, None
    for line in four_letter(name).splitlines():
        if line.startswith("Mode:"):
            mode = line.split(":", 1)[1].strip()
        elif line.startswith("Zxid:"):
            zxid = int(line.split(":", 1)[1].strip(), 16)
    return mode, zxid


def decode_zxid(zxid):
    """Split a zxid into (epoch, counter): epoch = high 32 bits, counter = low 32 bits."""
    return zxid >> 32, zxid & 0xFFFFFFFF


def now():
    """Wall-clock time in seconds (float), for logging and measuring durations."""
    return time.time()


def stamp():
    """Current time as HH:MM:SS.mmm, for log lines."""
    t = time.time()
    return time.strftime("%H:%M:%S", time.localtime(t)) + f".{int(t * 1000) % 1000:03d}"
