"""Part A3: take the lock, hold it for a while, then release it.

    python scripts/holder.py --name c1 --timeout 4      # terminal 1: c1 gets the lock
    python scripts/holder.py --name c2 --timeout 4      # terminal 2: c2 waits for it
    kill -9 <PID of c1>                               # terminal 3: crash c1

Every line is timestamped, and the script prints its PID so you can kill it.
"""
import argparse
import os
import time

from lib.zkutil import connect, stamp
from lock import LOCKS        # scripts/lock.py

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True, help="a name for this client, shown in its output")
ap.add_argument("--lock", choices=["v1", "v2"], default="v2")
ap.add_argument("--timeout", type=float, default=4.0, help="session timeout in seconds")
ap.add_argument("--hold", type=int, default=60, help="seconds to hold the lock")
a = ap.parse_args()

print(f"{stamp()} [{a.name}] pid={os.getpid()} session timeout={a.timeout}s", flush=True)
zk = connect(timeout=a.timeout)
def on_state(s):
    print(f"{stamp()} [{a.name}] session state -> {s}", flush=True)
zk.add_listener(on_state)

lock = LOCKS[a.lock](zk, "resource")
print(f"{stamp()} [{a.name}] waiting for lock", flush=True)
lock.acquire()
print(f"{stamp()} [{a.name}] ACQUIRED lock", flush=True)

for i in range(a.hold):
    if i % 5 == 0:
        print(f"{stamp()} [{a.name}] holding the lock ({i} s)", flush=True)
    time.sleep(1)

lock.release()
print(f"{stamp()} [{a.name}] released lock", flush=True)
zk.remove_listener(on_state)   # a normal close is not a failure; do not print it
zk.stop()
