"""Score cached predictions against gold labels.

    python3 -m eval.metrics          # prints the table, writes eval/results.json

Every model is reduced to the same prediction shape (see load_jev / load_llm), and warmth is composed by the
same code for every model, so differences come from the judgments alone.
"""
import csv
import json
import statistics
from pathlib import Path

import jevlib

ROOT = Path(__file__).resolve().parent.parent
CLASSES = ["soft_deferral", "hard_no", "went_quiet", "not_sales"]
MONTH_IX = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                             "September", "October", "November", "December"])}
AS_OF = (2026, 9)


def months_elapsed(sent):
    mon, yr = sent.split()
    return (AS_OF[0] - int(yr)) * 12 + (AS_OF[1] - MONTH_IX[mon])


def warmth(choice, sub):
    """Same composition as the page demo (jevlib.warmth), from 0..1 sub-scores."""
    clamp = lambda x, a, b: max(a, min(b, x))
    base = sum(w * sub[k] for k, w in jevlib.WEIGHTS.items())
    if choice == "soft_deferral":
        return round(clamp(base * 105, 10, 97))
    if choice == "went_quiet":
        return round(clamp((0.5 * sub["ripeness"] + 0.3 * sub["seniority"] + 0.2) * 100, 20, 72))
    if choice == "hard_no":
        return round(clamp(base * 12, 3, 16))
    return round(clamp(base * 6, 1, 9))


def ripeness(timeframe, elapsed):
    expected = jevlib.TIMEFRAME_MONTHS.get(timeframe)
    if expected is None:
        return max(0.15, min(1.0, elapsed / 20))
    return max(0.0, min(1.0, elapsed / expected))


def load_threads(folder=ROOT / "data"):
    return {json.loads(l)["id"]: json.loads(l) for l in open(Path(folder) / "threads.jsonl") if l.strip()}


def load_gold(folder=ROOT / "data"):
    rows = {}
    for r in csv.DictReader(open(Path(folder) / "labels.csv")):
        r["reopen_worthy"] = r["reopen_worthy"] == "True"
        r["near_miss"] = r["near_miss"] == "True"
        rows[r["id"]] = r
    return rows


def jev_pred(r):
    """One cached Jev response -> the shared prediction shape."""
    a = r["answers"]
    return {"choice": a["category"]["choice"], "probs": a["category"]["probabilities"],
            "timeframe": a["awaited_timeframe"]["choice"],
            "trigger": jevlib.unit(a["trigger_clarity"]), "seniority": jevlib.unit(a["seniority"]),
            "named_trigger": a["named_trigger"]["noul"],
            "in_tok": r["usage"]["input_tokens"], "out_tok": r["usage"]["output_tokens"], "latency_s": r["latency_s"]}


def llm_pred(r):
    """One cached baseline response -> the shared prediction shape."""
    return r["pred"] | {"in_tok": r["usage"]["input_tokens"], "out_tok": r["usage"]["output_tokens"],
                        "latency_s": r["latency_s"]}


def load_jev():
    preds = {}
    for f in sorted((ROOT / "jev/cache").glob("t*.json")):
        preds[f.stem] = jev_pred(json.loads(f.read_text()))
    meta = json.loads((ROOT / "jev/run_meta.json").read_text())
    meta["model_id"] = sorted({json.loads(f.read_text())["model"] for f in (ROOT / "jev/cache").glob("t*.json")})[-1]
    return preds, meta, {"in": jevlib.PRICE_PER_MTOK, "out": 0.0}


def load_llm():
    d = ROOT / "baseline/cache"
    meta_f = ROOT / "baseline/run_meta.json"
    if not meta_f.exists():
        return None
    meta = json.loads(meta_f.read_text())
    preds = {}
    for f in sorted(d.glob("t*.json")):
        preds[f.stem] = llm_pred(json.loads(f.read_text()))
    return preds, meta, meta["price_per_mtok"]


def ece(points, bins=10):
    """Expected calibration error on the top-class probability, plus the reliability curve."""
    curve, total, err = [], len(points), 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [(p, ok) for p, ok in points if (lo < p <= hi) or (b == 0 and p == 0)]
        if not sel:
            continue
        conf = sum(p for p, _ in sel) / len(sel)
        acc = sum(ok for _, ok in sel) / len(sel)
        err += len(sel) / total * abs(acc - conf)
        curve.append({"conf": round(conf, 3), "acc": round(acc, 3), "n": len(sel)})
    return err, curve


def evaluate(name, preds, meta, price, gold, threads):
    ids = sorted(gold)
    missing = [i for i in ids if i not in preds]
    assert not missing, f"{name}: {len(missing)} threads have no prediction"
    rows = []
    for i in ids:
        p, g = preds[i], gold[i]
        el = months_elapsed(threads[i]["last_message_sent"])
        sub = {"trigger": p["trigger"], "seniority": p["seniority"], "ripeness": ripeness(p["timeframe"], el)}
        top = max(p["probs"].values())
        rows.append({"id": i, "gold": g["label"], "pred": p["choice"], "top_p": top, "warmth": warmth(p["choice"], sub),
                     "reopen": g["reopen_worthy"], "near": g["near_miss"], "tf_ok": p["timeframe"] == g["timeframe"]})
    tp = sum(r["pred"] == r["gold"] == "soft_deferral" for r in rows)
    pp = sum(r["pred"] == "soft_deferral" for r in rows)
    gp = sum(r["gold"] == "soft_deferral" for r in rows)
    ranked = sorted(rows, key=lambda r: (-r["warmth"], r["id"]))
    e, curve = ece([(r["top_p"], r["pred"] == r["gold"]) for r in rows])
    in_tok = sum(p["in_tok"] for p in preds.values())
    out_tok = sum(p["out_tok"] for p in preds.values())
    cost = in_tok / 1e6 * price["in"] + out_tok / 1e6 * price["out"]
    n = len(rows)
    near = [r for r in rows if r["near"]]
    defs = [r for r in rows if r["gold"] == "soft_deferral"]
    share = lambda hits, pool: hits / pool if pool else 0.0
    k10, k30 = min(10, n), min(30, n)
    return {
        "model": meta.get("model_id", meta.get("model")), "n": n,
        "accuracy": sum(r["pred"] == r["gold"] for r in rows) / n,
        "near_miss_accuracy": share(sum(r["pred"] == r["gold"] for r in near), len(near)),
        "deferral_precision": share(tp, pp), "deferral_recall": share(tp, gp),
        "precision_at_10": share(sum(r["reopen"] for r in ranked[:k10]), k10),
        "precision_at_30": share(sum(r["reopen"] for r in ranked[:k30]), k30),
        "timeframe_accuracy_on_deferrals": share(sum(r["tf_ok"] for r in defs), len(defs)),
        "ece": e, "reliability": curve,
        "confusion": {g: {p: sum(r["gold"] == g and r["pred"] == p for r in rows) for p in CLASSES} for g in CLASSES},
        "cost_usd_run": cost, "cost_usd_per_10k": cost / n * 10_000,
        "in_tokens": in_tok, "out_tokens": out_tok,
        "median_call_s": statistics.median(p["latency_s"] for p in preds.values()),
        "wall_s_run": meta["wall_s"], "workers": meta["workers"],
        "wall_s_per_10k": meta["wall_s"] / n * 10_000,  # extrapolated at the same concurrency
        "top10": [(r["id"], r["warmth"], r["gold"], r["reopen"]) for r in ranked[:10]],
    }


def main():
    gold, threads = load_gold(), load_threads()
    results = {"jev": evaluate("jev", *load_jev(), gold, threads)}
    llm = load_llm()
    if llm:
        results["llm"] = evaluate("llm", *llm, gold, threads)
    (ROOT / "eval/results.json").write_text(json.dumps(results, indent=2))
    keys = ["accuracy", "near_miss_accuracy", "deferral_precision", "deferral_recall", "precision_at_10", "precision_at_30",
            "timeframe_accuracy_on_deferrals", "ece", "cost_usd_per_10k", "median_call_s", "wall_s_per_10k"]
    print(f"{'metric':34}" + "".join(f"{k:>14}" for k in results))
    for k in keys:
        print(f"{k:34}" + "".join(f"{v[k]:>14.4f}" for v in results.values()))
    for name, v in results.items():
        print(f"\n{name} ({v['model']}) confusion, rows = gold:")
        print(" " * 15 + "".join(f"{c[:12]:>13}" for c in CLASSES))
        for g in CLASSES:
            print(f"{g:15}" + "".join(f"{v['confusion'][g][c]:>13}" for c in CLASSES))
        print("reliability:", v["reliability"])
        print("top10:", v["top10"])


if __name__ == "__main__":
    main()
