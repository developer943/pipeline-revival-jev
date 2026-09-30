"""Mock inbox for the Dated, Not Dead test.

Load a dataset of dead email threads, run Jev and the LLM baseline over it, see the ranked reopen list,
and read off the newsletter's §05-§06 numbers.

    .venv/bin/python app/server.py                  # then open http://127.0.0.1:8765
    .venv/bin/python app/server.py --data datasets/mine --as-of 2026-10

A dataset is a folder holding threads.jsonl (one thread per line) and labels.csv (the answer key);
app/README.md has the format. Keys are read from .env and only ever sent to TypeSafe and Google.
Every answer is cached under runs/, keyed by thread id and content: re-runs are free, and editing a
thread re-runs just that thread.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import jevlib  # noqa: E402
from baseline import run_gemini  # noqa: E402  (stdlib only)
from eval import metrics  # noqa: E402

CLASSES = metrics.CLASSES
TIMEFRAMES = list(jevlib.QUESTIONS["awaited_timeframe"]["criteria"])
MONTHS = list(metrics.MONTH_IX)
RUNS = ROOT / "runs"
WORKERS = 8  # same concurrency for both models, so wall-clock times compare fairly
LABEL_COLUMNS = ["id", "label", "timeframe", "near_miss", "reopen_worthy"]
EDIT_FIELDS = ["label", "timeframe", "near_miss", "reopen_worthy"]
EDITS_FILE = "answer_key_edits.json"  # corrections made in the app, kept apart from labels.csv

# The LLM baseline, called "llm" in the API and on the page. It keeps its answer cache under runs/<store>/.
BASELINES = {
    "gemini": {"label": "Gemini", "store": "gemini", "key": "GEMINI_API_KEY", "workers": run_gemini.WORKERS,
               "model": run_gemini.MODEL, "price": run_gemini.PRICE, "old_cache": "baseline/cache_gemini",
               "old_meta": "baseline/run_meta_gemini.json"},
}
BASELINE = BASELINES["gemini"]


# ---------- keys ----------

def env_key(name):
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"') or None
    return None


# ---------- dataset ----------

def state_of(t):
    return {k: t[k] for k in ("contact_role", "last_message_sent", "messages")}


def state_hash(t):
    return hashlib.sha256(json.dumps(state_of(t), sort_keys=True).encode()).hexdigest()[:10]


def load_dataset(folder):
    """Threads + answer key, with every problem collected as a readable error instead of a crash."""
    folder = Path(folder)
    errors, threads, gold = [], {}, {}
    tpath, lpath = folder / "threads.jsonl", folder / "labels.csv"
    if not tpath.exists():
        return {"threads": {}, "gold": {}, "errors": [f"{tpath} not found"], "sha": None}
    for n, line in enumerate(tpath.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            t = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"threads.jsonl line {n}: not valid JSON ({e.msg})")
            continue
        missing = [k for k in ("id", "contact_role", "last_message_sent", "messages") if k not in t]
        if missing:
            errors.append(f"threads.jsonl line {n}: missing {', '.join(missing)}")
            continue
        if t["id"] in threads:
            errors.append(f"threads.jsonl line {n}: duplicate id {t['id']}")
            continue
        parts = str(t["last_message_sent"]).split()
        if len(parts) != 2 or parts[0] not in MONTHS or not parts[1].isdigit():
            errors.append(f"{t['id']}: last_message_sent must look like \"June 2026\"")
            continue
        if not isinstance(t["messages"], list) or not t["messages"] or \
                not all(isinstance(m, dict) and "from" in m and "text" in m for m in t["messages"]):
            errors.append(f"{t['id']}: messages must be a list of {{\"from\", \"text\"}}")
            continue
        threads[t["id"]] = t
    if lpath.exists():
        reader = csv.DictReader(lpath.read_text(encoding="utf-8").splitlines())
        absent = [c for c in LABEL_COLUMNS if c not in (reader.fieldnames or [])]
        if absent:
            errors.append(f"labels.csv is missing columns: {', '.join(absent)}")
        else:
            for r in reader:
                tid = r["id"]
                bad = []
                if tid not in threads:
                    bad.append("id not in threads.jsonl")
                if r["label"] not in CLASSES:
                    bad.append(f"label must be one of {', '.join(CLASSES)}")
                if r["timeframe"] not in TIMEFRAMES:
                    bad.append(f"timeframe must be one of {', '.join(TIMEFRAMES)}")
                for b in ("near_miss", "reopen_worthy"):
                    if r[b] not in ("True", "False"):
                        bad.append(f"{b} must be True or False")
                if bad:
                    errors.append(f"labels.csv {tid}: " + "; ".join(bad))
                    continue
                gold[tid] = r | {"near_miss": r["near_miss"] == "True", "reopen_worthy": r["reopen_worthy"] == "True"}
    # Corrections made in the app. Each is pinned to the thread's content, so an edit never lands on a different
    # thread after the dataset is rebuilt, and it records whether a model had already answered that thread.
    edits = read_edits(folder)
    for tid, e in edits.items():
        t = threads.get(tid)
        if not t or e.get("thread_hash") != state_hash(t):
            errors.append(f"{EDITS_FILE}: the correction for {tid} no longer matches that thread, so it was not applied")
            continue
        gold[tid] = gold.get(tid, {"id": tid}) | {k: e[k] for k in EDIT_FIELDS} | \
            {"edited": True, "edited_after_run": e["after_run"], "was": e.get("was")}
    unlabelled = [i for i in threads if i not in gold]
    if gold and unlabelled:
        errors.append(f"{len(unlabelled)} threads have no label (e.g. {unlabelled[0]}); they are left out of scoring")
    return {"threads": threads, "gold": gold, "errors": errors, "folder": folder,
            "sha": hashlib.sha256(tpath.read_bytes()).hexdigest()}


def read_edits(folder):
    p = Path(folder) / EDITS_FILE
    return json.loads(p.read_text()) if p.exists() else {}


def save_edit(ds, req):
    """Record one answer-key correction (or undo it with revert=True)."""
    tid = req["id"]
    t = ds["threads"][tid]
    edits = read_edits(ds["folder"])
    if req.get("revert"):
        edits.pop(tid, None)
    else:
        if req["label"] not in CLASSES or req["timeframe"] not in TIMEFRAMES:
            raise ValueError("label or timeframe is not an allowed value")
        if tid in edits:  # keep the original labels.csv answer, not the previous correction
            prev = edits[tid].get("was")
        else:
            prev = {k: ds["gold"][tid][k] for k in EDIT_FIELDS} if tid in ds["gold"] else None
        edits[tid] = {"label": req["label"], "timeframe": req["timeframe"],
                      "near_miss": bool(req["near_miss"]), "reopen_worthy": bool(req["reopen_worthy"]),
                      "after_run": any(read_cached(m, t) is not None for m in ("jev", "llm")),
                      "was": prev, "thread_hash": state_hash(t), "changed": time.strftime("%Y-%m-%d %H:%M")}
    path = Path(ds["folder"]) / EDITS_FILE
    if edits:
        path.write_text(json.dumps(edits, indent=1))
    elif path.exists():
        path.unlink()


# ---------- answer cache ----------

def store(model):
    return "jev" if model == "jev" else BASELINE["store"]


def cache_path(model, t, where=None):
    return RUNS / (where or store(model)) / f"{t['id']}-{state_hash(t)}.json"


def meta_path(model, ds, where=None):
    return RUNS / (where or store(model)) / f"meta-{ds['sha'][:12]}.json"


def read_cached(model, t):
    p = cache_path(model, t)
    return json.loads(p.read_text()) if p.exists() else None


def import_earlier_runs(ds):
    """Reuse jev/cache and baseline/cache when they were produced from this exact threads.jsonl."""
    marker = ROOT / "jev/cache_source.json"
    if not ds["sha"] or not marker.exists() or json.loads(marker.read_text())["threads_sha256"] != ds["sha"]:
        return
    sources = [("jev", ROOT / "jev/cache", ROOT / "jev/run_meta.json")] + \
        [(b["store"], ROOT / b["old_cache"], ROOT / b["old_meta"]) for b in BASELINES.values()]
    for where, old_dir, old_meta in sources:
        copied = 0
        for t in ds["threads"].values():
            src, dst = old_dir / f"{t['id']}.json", cache_path(None, t, where)
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
                copied += 1
        if copied and old_meta.exists() and not meta_path(None, ds, where).exists():
            m = json.loads(old_meta.read_text())
            meta_path(None, ds, where).write_text(json.dumps({"wall_s": m["wall_s"], "workers": m["workers"], "calls": m["threads"]}))


def to_pred(model, rec):
    return metrics.jev_pred(rec) if model == "jev" else metrics.llm_pred(rec)


def price(model):
    if model == "jev":
        return {"in": jevlib.PRICE_PER_MTOK, "out": 0.0}
    return BASELINE["price"]


def view(model, rec, t):
    """What the inbox shows for one answer: the prediction plus warmth, composed exactly as eval/metrics does."""
    if rec is None:
        return None
    p = to_pred(model, rec)
    el = metrics.months_elapsed(t["last_message_sent"])
    sub = {"trigger": p["trigger"], "seniority": p["seniority"], "ripeness": metrics.ripeness(p["timeframe"], el)}
    pr = price(model)
    return {"choice": p["choice"], "probs": p["probs"], "confidence": max(p["probs"].values()),
            "timeframe": p["timeframe"], "named_trigger": p["named_trigger"], "sub": sub,
            "warmth": metrics.warmth(p["choice"], sub), "latency_s": p["latency_s"],
            "cost_usd": p["in_tok"] / 1e6 * pr["in"] + p["out_tok"] / 1e6 * pr["out"],
            "model": rec.get("model"), "note": rec.get("note")}


# ---------- model calls ----------

class Caller:
    def jev(self, t):
        return jevlib.ask(state_of(t), key=env_key("TYPESAFE_API_KEY") or jevlib.load_key())

    def llm(self, t):
        return run_gemini.call(t, key=env_key("GEMINI_API_KEY"))

    def __call__(self, model, t):
        return self.jev(t) if model == "jev" else self.llm(t)


class Job:
    """One background batch at a time: run a model over every thread that has no cached answer yet."""

    def __init__(self, caller):
        self.caller, self.lock = caller, threading.Lock()
        self.state = {"running": False, "model": None, "done": 0, "total": 0, "errors": [], "wall_s": 0.0}

    def snapshot(self):
        with self.lock:
            return dict(self.state, errors=self.state["errors"][-20:])

    def start(self, model, ds):
        with self.lock:
            if self.state["running"]:
                return "A run is already in progress"
            todo = [t for t in ds["threads"].values() if read_cached(model, t) is None]
            self.state = {"running": True, "model": model, "done": 0, "total": len(todo), "errors": [], "wall_s": 0.0, "skipped": 0}
        threading.Thread(target=self._run, args=(model, ds, todo), daemon=True).start()
        return None

    def _run(self, model, ds, todo):
        stop = []  # set once a daily quota is used up: the rest of the batch cannot succeed today

        def one(t):
            if stop:
                with self.lock:
                    self.state["done"] += 1
                    self.state["skipped"] += 1
                return
            try:
                rec = self.caller(model, t)
                path = cache_path(model, t)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(rec))
            except run_gemini.QuotaExhausted as e:
                with self.lock:
                    if not stop:
                        self.state["errors"].append(f"Stopped at {t['id']}: {e}")
                    stop.append(True)
            except BaseException as e:  # jevlib raises SystemExit on HTTP errors; keep the batch going
                with self.lock:
                    self.state["errors"].append(f"{t['id']}: {e}")
            with self.lock:
                self.state["done"] += 1
                self.state["wall_s"] = round(time.perf_counter() - t0, 2)

        workers = WORKERS if model == "jev" else BASELINE["workers"]
        t0 = time.perf_counter()
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(one, todo))
        wall = time.perf_counter() - t0
        ok = sum(1 for t in todo if read_cached(model, t) is not None)
        if ok:
            mp = meta_path(model, ds)
            m = json.loads(mp.read_text()) if mp.exists() else {"wall_s": 0.0, "workers": workers, "calls": 0}
            m["wall_s"] = round(m["wall_s"] + wall, 2)
            m["calls"] += ok
            mp.parent.mkdir(parents=True, exist_ok=True)
            mp.write_text(json.dumps(m))
        with self.lock:
            self.state["running"] = False
            self.state["wall_s"] = round(wall, 2)


# ---------- results ----------

def results(ds):
    out = {"models": {}, "slots": {}}
    gold, threads = ds["gold"], ds["threads"]
    if not gold:
        return out
    for model in ("jev", "llm"):
        recs = {i: read_cached(model, threads[i]) for i in gold}
        done = {i: r for i, r in recs.items() if r is not None}
        if not done:
            continue
        mp = meta_path(model, ds)
        meta = json.loads(mp.read_text()) if mp.exists() else {"wall_s": 0.0, "workers": WORKERS, "calls": len(done)}
        # wall time is recorded per batch; scale it to the scored threads so a partial run still extrapolates
        wall_per_thread = meta["wall_s"] / max(1, meta["calls"])
        meta = {"model_id": sorted({r.get("model") or "" for r in done.values()})[-1],
                "wall_s": wall_per_thread * len(done), "workers": meta["workers"]}
        preds = {i: to_pred(model, r) for i, r in done.items()}
        res = metrics.evaluate(model, preds, meta, price(model), {i: gold[i] for i in done}, threads)
        misses = [{"id": i, "gold": gold[i]["label"], "pred": preds[i]["choice"], "confidence": max(preds[i]["probs"].values()),
                   "near_miss": gold[i]["near_miss"], "text": threads[i]["messages"][-1]["text"][:220]}
                  for i in sorted(done) if preds[i]["choice"] != gold[i]["label"]]
        res.update({"scored": len(done), "of": len(gold), "misses": misses,
                    "refusals": sum(1 for r in done.values() if r.get("note"))})
        out["models"][model] = res
    edited = [i for i, g in gold.items() if g.get("edited")]
    out["edits"] = {"total": len(edited), "after_run": sorted(i for i in edited if gold[i]["edited_after_run"])}
    out["slots"] = slots(ds, out["models"])
    if out["edits"]["after_run"]:
        n = len(out["edits"]["after_run"])
        out["slots"]["_edits"] = (f"{n} answer{' was' if n == 1 else 's were'} changed after a model had answered "
                                  f"({', '.join(out['edits']['after_run'][:5])}). Say so in the write-up.")
    out["dataset"] = {"threads": len(threads), "labelled": len(gold), "as_of": list(metrics.AS_OF)}
    out["generated"] = time.strftime("%Y-%m-%d %H:%M")
    # a copy next to the dataset, so the numbers can be read (and committed) without the app running;
    # rewritten only when the numbers change, not for a new timestamp
    path = Path(ds["folder"]) / "results.json"
    try:
        old = json.loads(path.read_text())
    except (OSError, ValueError):
        old = None
    fresh = json.loads(json.dumps(out))  # tuples → lists, so it compares like the file does
    if old is None or {k: v for k, v in old.items() if k != "generated"} != {k: v for k, v in fresh.items() if k != "generated"}:
        path.write_text(json.dumps(out, indent=1))
    return out


def slots(ds, models):
    gold = ds["gold"]
    split = {c: sum(g["label"] == c for g in gold.values()) for c in CLASSES}
    s = {"DATASET_SIZE": str(len(gold)),
         "LABEL_SPLIT": " · ".join(f"{split[c]} {c}" for c in CLASSES),
         "NEAR_MISSES": f"{sum(g['near_miss'] for g in gold.values())} near-misses"}
    j, l = models.get("jev"), models.get("llm")
    if l:
        s["BASELINE_MODEL"] = l["model"]
    if j:
        s["DEFERRAL_PRECISION / DEFERRAL_RECALL"] = f"{j['deferral_precision']:.2f} / {j['deferral_recall']:.2f}"
        k = min(10, j["scored"])
        s["PRECISION_AT_10"] = f"{round(j['precision_at_10'] * k)} / {k}"
        s["ECE"] = f"{j['ece']:.3f}"
        s["COST_JEV"] = f"${j['cost_usd_per_10k']:.2f} per 10k threads"
        s["LATENCY_JEV"] = f"{j['median_call_s']:.2f}s per thread (median) · {j['wall_s_per_10k'] / 60:.1f} min per 10k"
        pairs = {}
        for m in j["misses"]:
            pairs.setdefault((m["gold"], m["pred"]), []).append(m["id"])
        top = sorted(pairs.items(), key=lambda kv: -len(kv[1]))[:3]
        if top:
            s["JEV_MISSES"] = "; ".join(f"{len(ids)}× {g} read as {p} (e.g. {ids[0]})" for (g, p), ids in top)
    if l:
        s["COST_LLM"] = f"${l['cost_usd_per_10k']:.2f} per 10k threads"
        s["LATENCY_LLM"] = f"{l['median_call_s']:.2f}s per thread (median) · {l['wall_s_per_10k'] / 60:.1f} min per 10k"
    if j and j["scored"] < j["of"]:
        s["_note"] = f"Jev has scored {j['scored']} of {j['of']} threads; numbers are provisional until the run finishes."
    return s


# ---------- HTTP ----------

class App:
    def __init__(self, data, as_of):
        self.data, self.as_of = Path(data), as_of
        metrics.AS_OF = as_of
        self.caller = Caller()
        self.job = Job(self.caller)

    def dataset(self):
        ds = load_dataset(self.data)
        import_earlier_runs(ds)
        return ds

    def payload(self):
        ds = self.dataset()
        rows = []
        for t in ds["threads"].values():
            rows.append({"id": t["id"], "contact_role": t["contact_role"], "last_message_sent": t["last_message_sent"],
                         "months_elapsed": metrics.months_elapsed(t["last_message_sent"]), "messages": t["messages"],
                         "gold": ds["gold"].get(t["id"]),
                         "jev": view("jev", read_cached("jev", t), t), "llm": view("llm", read_cached("llm", t), t)})
        return {"dataset": str(self.data.resolve().relative_to(ROOT)) if self.data.resolve().is_relative_to(ROOT) else str(self.data),
                "as_of": f"{MONTHS[self.as_of[1] - 1]} {self.as_of[0]}", "errors": ds["errors"], "threads": rows,
                "has_labels": bool(ds["gold"]), "job": self.job.snapshot(),
                "ready": {"jev": bool(env_key("TYPESAFE_API_KEY")), "llm": self.baseline_ready()},
                "baseline": {"label": BASELINE["label"], "model": BASELINE["model"], "hint": self.baseline_hint()}}

    def baseline_ready(self):
        return bool(env_key(BASELINE["key"]))

    def baseline_hint(self):
        if self.baseline_ready():
            return ""
        return f"Add {BASELINE['key']}=… to .env and restart."


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/data":
                return self.send(200, app.payload())
            if self.path == "/api/job":
                return self.send(200, app.job.snapshot())
            if self.path == "/api/results":
                return self.send(200, results(app.dataset()))
            if self.path == "/api/results/download":
                data = json.dumps(results(app.dataset()), indent=1).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Disposition", 'attachment; filename="results.json"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                return self.wfile.write(data)
            self.send(404, {"error": "not found"})

        def do_POST(self):
            # Browsers send an Origin on cross-site POSTs; refuse anything that isn't this page.
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                return self.send(403, {"error": "cross-origin request refused"})
            try:
                req = self.body()
                if self.path == "/api/run-all":
                    err = app.job.start(req["model"], app.dataset())
                    return self.send(409 if err else 200, {"error": err} if err else app.job.snapshot())
                if self.path == "/api/run-one":
                    ds = app.dataset()
                    t = ds["threads"][req["id"]]
                    rec = app.caller(req["model"], t)
                    p = cache_path(req["model"], t)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(json.dumps(rec))
                    return self.send(200, view(req["model"], rec, t))
                if self.path == "/api/label":
                    save_edit(app.dataset(), req)
                    return self.send(200, {"ok": True})
                if self.path == "/api/try":
                    t = {"id": "pasted", "contact_role": req.get("contact_role") or "unknown",
                         "last_message_sent": req["last_message_sent"],
                         "messages": [{"from": "seller (me)" if req.get("last_from_seller") else (req.get("contact_role") or "buyer"),
                                       "text": req["text"]}]}
                    return self.send(200, view("jev", app.caller("jev", t), t))
            except BaseException as e:  # SystemExit from jevlib carries the API's error text
                return self.send(500, {"error": str(e)})
            self.send(404, {"error": "not found"})

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(ROOT / "data"), help="folder with threads.jsonl and labels.csv")
    ap.add_argument("--as-of", default="2026-09", help="the month your test is 'today', YYYY-MM (for timing ripeness)")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    y, m = (int(x) for x in a.as_of.split("-"))
    app = App(a.data, (y, m))
    server = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(app))
    print(f"Mock inbox on http://127.0.0.1:{a.port}  ·  dataset: {a.data}  ·  as of {a.as_of}  ·  "
          f"baseline: {BASELINE['label']} ({BASELINE['model']})  ·  Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
