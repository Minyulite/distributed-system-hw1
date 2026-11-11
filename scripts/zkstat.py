"""Show each server's role and last zxid.

    python scripts/zkstat.py          # once
    python scripts/zkstat.py --watch  # refresh every second (Ctrl-C to stop)
"""
import sys
import time

from lib.zkutil import SERVERS, decode_zxid, server_state, stamp


def show():
    print(f"--- {stamp()}")
    for n in SERVERS:
        mode, zxid = server_state(n)
        if mode is None:
            print(f"{n}: not serving (down, starting, or looking for a leader)")
        else:
            e, c = decode_zxid(zxid)
            print(f"{n}: {mode:10} zxid=0x{zxid:x}  (epoch {e}, counter {c})")


if __name__ == "__main__":
    if "--watch" in sys.argv:
        try:
            while True:
                show()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        show()
