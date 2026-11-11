# hw1_coordination: ZooKeeper Homework (Coordination)

2110318 Distributed Systems Essentials. **The tasks, questions and grading are in the handout.**
This file explains how to run things.

## 1. Requirements
- Docker Desktop (Windows/macOS) or Docker Engine + Compose v2 (Linux). Give Docker at least 2 GB of RAM.
- The first start downloads about 350 MB of images.

## 2. Start, stop, reset
On the host, in this folder:
```bash
docker compose up -d                                  # start 3 ZooKeeper servers + storage + dev
docker compose exec dev bash                          # open a shell in the dev container; run ALL python here
docker compose down -v                                # stop everything and delete all ZooKeeper data
```
Wait about 20 seconds after `up`, then check inside `dev` that one server is the leader:
```bash
python scripts/zkstat.py
```
Open more terminals with `docker compose exec dev bash` when a task needs several processes (A3 needs 3).

## 3. What is where
Everything you run, read or edit is in `scripts/`. `lib/` holds support code: your scripts import it,
but you never need to change it.

| Path | What it is |
|---|---|
| `scripts/lock.py` | `NoLock`, `LockV1` (given). **TODO A2: `LockV2`** |
| `scripts/counter_test.py` | A1, A2: W worker processes each add 1 to the shared counter N times |
| `scripts/holder.py` | A3: take the lock, print the PID, hold the lock for 60 s |
| `scripts/zkstat.py` | role and zxid of each server |
| `lib/zkutil.py` | `connect(...)`, `server_state(...)`, `stamp()` helpers |
| `lib/storage_client.py` | `get_counter()`, `put_counter(v)`, `reset()` |
| `lib/storage_server.py` | the storage service: one shared counter (runs in the `storage` container) |
| `docker-compose.yml` | `zk1`–`zk3` (ZooKeeper 3.9), `storage`, `dev`, all on one network |

Only change `scripts/lock.py`.

## 4. Commands you will use
Inside `dev`:
```bash
python scripts/counter_test.py --lock none            # A1
python scripts/counter_test.py --lock v1 --workers 5  # A1 (also --workers 2, 10)
python scripts/counter_test.py --lock v2 --workers 5  # A2
python scripts/holder.py --name c1 --timeout 4        # A3
kill -9 <PID>                                         # crash a process
```
On the host:
```bash
docker logs zk1                                       # a server's log
```

## 5. Troubleshooting
- **`ConnectionLoss` or a hang right after `up`**: the servers are still electing a leader. Wait and run `zkstat.py`.
- **`counter_test.py` hangs with `--lock v2`**: your `acquire()` never returns. Press Ctrl-C, then check that
  each waiter watches its predecessor and lists the children again after every notification.
- **"container name ... is already in use"**: another Docker project with the same container names is still running. Run `docker compose down -v` in its folder.
- **Leftover state from a previous run**: `docker compose down -v && docker compose up -d`.
- **Kazoo prints long tracebacks while a server is down**: this is Kazoo retrying. Look at the lines your script prints.
