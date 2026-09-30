"""Run Jev over data/threads.jsonl. Every response is cached in jev/cache/, so re-runs cost nothing.

    python3 -m jev.run_jev           # uses TYPESAFE_API_KEY from .env
"""
import json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import jevlib

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "jev/cache"
WORKERS = 8  # same concurrency as the baseline, so wall-clock times compare fairly


def state_of(thread):
    return {k: thread[k] for k in ("contact_role", "last_message_sent", "messages")}


def main():
    threads = [json.loads(l) for l in open(ROOT / "data/threads.jsonl")]
    todo = [t for t in threads if not (CACHE / f"{t['id']}.json").exists()]
    key = jevlib.load_key() if todo else None

    def one(t):
        r = jevlib.ask(state_of(t), key=key)
        (CACHE / f"{t['id']}.json").write_text(json.dumps(r))
        return r

    t0 = time.perf_counter()
    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(one, todo))
    wall = time.perf_counter() - t0
    if todo:
        (ROOT / "jev/run_meta.json").write_text(json.dumps({"threads": len(todo), "workers": WORKERS, "wall_s": round(wall, 2),
                                                             "model": jevlib.MODEL, "finished": time.strftime("%Y-%m-%d %H:%M")}))
    print(f"{len(todo)} new calls in {wall:.1f}s ({len(threads) - len(todo)} cached)")


if __name__ == "__main__":
    main()
