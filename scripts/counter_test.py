"""Parts A1 and A2: W workers each add 1 to a shared counter N times, using a lock.

    python scripts/counter_test.py --lock none
    python scripts/counter_test.py --lock v1 --workers 5 --n 100
    python scripts/counter_test.py --lock v2 --workers 5 --n 100

The counter lives in the storage service and is updated with a read-modify-write
(GET then PUT), which is only correct if the lock really gives mutual exclusion.
Each worker is a separate process with its own ZooKeeper session.
"""
import argparse
import multiprocessing as mp
import time

from lib import storage_client as st
from lib.zkutil import connect
from lock import LOCKS        # scripts/lock.py


def worker(lock_kind, n, results):
    zk = connect()
    lock = LOCKS[lock_kind](zk, "counter")
    for _ in range(n):
        lock.acquire()
        v = st.get_counter()
        st.put_counter(v + 1)
        lock.release()
    results.put(lock.wakeups)
    zk.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", choices=LOCKS, required=True)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()

    st.reset()
    results = mp.Queue()
    procs = [mp.Process(target=worker, args=(a.lock, a.n, results)) for _ in range(a.workers)]
    t0 = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    elapsed = time.time() - t0
    if any(p.exitcode != 0 for p in procs):
        raise SystemExit("a worker crashed (see the traceback above)")
    wakeups = sum(results.get() for _ in procs)
    expected = a.workers * a.n
    got = st.get_counter()
    print(f"lock={a.lock} workers={a.workers} n={a.n}")
    print(f"counter = {got} (expected {expected}, lost updates = {expected - got})")
    print(f"total wakeups = {wakeups}, wakeups per acquisition = {wakeups / expected:.2f}")
    print(f"elapsed = {elapsed:.1f} s")
