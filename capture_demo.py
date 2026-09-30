"""Run real Jev on the 7 demo threads in dated-not-dead.html and save the answers the page
will embed. Usage: python3 capture_demo.py [--dry-run]"""
import json, re, sys, datetime
from pathlib import Path
import jevlib

PAGE = Path.home() / "Desktop/dated-not-dead.html"


def samples_from_page():
    js = PAGE.read_text().split("var samples = [", 1)[1].split("];", 1)[0]
    out = []
    for m in re.finditer(r"\{id:'(\w+)', who:'([^']*)', role:'([^']*)', date:'([^']*)', ageMo:(\d+), lastFromSeller:(true|false),\s*text:\"((?:[^\"\\]|\\.)*)\"\}", js):
        out.append({"id": m[1], "who": m[2], "role": m[3], "date": m[4], "ageMo": int(m[5]),
                    "lastFromSeller": m[6] == "true", "text": re.sub(r"\\(.)", r"\1", m[7])})
    return out


def main():
    samples = samples_from_page()
    assert len(samples) == 7, f"parsed {len(samples)} samples from page"
    if "--dry-run" in sys.argv:
        print(json.dumps({"state": jevlib.state_for(samples[0]), "model": jevlib.MODEL,
                          "questions": list(jevlib.QUESTIONS)}, indent=2, ensure_ascii=False))
        return
    key = jevlib.load_key()
    rows, tokens = {}, 0
    for s in samples:
        state = jevlib.state_for(s)
        r = jevlib.ask(state, key=key)
        a = r["answers"]
        tokens += r["usage"]["input_tokens"]
        rows[s["id"]] = {
            "text": s["text"],
            "choice": a["category"]["choice"], "probs": a["category"]["probabilities"],
            "confidence": a["category"]["confidence"],
            "noulTrigger": a["named_trigger"]["noul"], "noulQuiet": a["seller_unanswered"]["noul"],
            "timeframe": a["awaited_timeframe"]["choice"],
            "sub": jevlib.subscores(a, s["ageMo"]),
            "warmth": jevlib.warmth(a, s["ageMo"]), "latency_s": r["latency_s"], "input_tokens": r["usage"]["input_tokens"],
            "playground": jevlib.playground_link(state),
        }
        print(f"{s['id']:7} {rows[s['id']]['choice']:14} conf={rows[s['id']]['confidence']:.2f} "
              f"trig={rows[s['id']]['noulTrigger']:.2f} quiet={rows[s['id']]['noulQuiet']:.2f} "
              f"warmth={rows[s['id']]['warmth']:3}  {r['latency_s']:.2f}s  model={r['model']}")
    meta = {"model": r["model"], "captured": datetime.date.today().isoformat(), "input_tokens": tokens,
            "cost_usd": tokens / 1e6 * jevlib.PRICE_PER_MTOK}
    Path("demo_jev.json").write_text(json.dumps({"meta": meta, "threads": rows}, indent=2, ensure_ascii=False))
    print(f"\n{tokens} input tokens, ${meta['cost_usd']:.6f} total -> demo_jev.json")


if __name__ == "__main__":
    main()
