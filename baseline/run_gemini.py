"""Same task on Google Gemini (structured JSON output): a baseline from a different model family than the one that
drafted the test set. Cached per thread.

    python3 -m baseline.run_gemini          # GEMINI_API_KEY from .env; GEMINI_MODEL=... picks another model

Gemini gets the same threads and question definitions as Jev, with one system prompt and output schema
(baseline/prompt.py). Stdlib only. No fallback: a blocked, truncated or unparseable answer is recorded as such and
scored as wrong.
"""
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from baseline.prompt import REFUSED, SCHEMA, SYSTEM, prompt_for, to_pred

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "baseline/cache_gemini"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
THINKING = "low"  # a classification task, so low thinking
# $/Mtok, Gemini API paid-tier list price for gemini-3.8-flash (ai.google.dev/gemini-api/docs/pricing, read 2026-09-30;
# it rises to $1.50 / $7.50 on 2027-01-01). Thinking tokens bill as output. Free-tier calls cost nothing, but the
# comparison uses the paid price.
PRICE = {"in": 0.75, "out": 3.75}
WORKERS = int(os.environ.get("GEMINI_WORKERS", 8))  # same parallelism as Jev on a paid tier; set 2 on the free tier
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def load_key():
    key = os.environ.get("GEMINI_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
    if not key:
        raise SystemExit("GEMINI_API_KEY is empty. Add it to .env in the repo folder")
    return key


class QuotaExhausted(RuntimeError):
    """A per-day quota is used up: retrying within the run cannot succeed."""


def _daily_quota(err_body):
    try:
        for d in json.loads(err_body)["error"].get("details", []):
            for v in d.get("violations", []):
                if "PerDay" in v.get("quotaId", ""):
                    return f"{v.get('quotaValue', '?')} requests per day ({v['quotaId']})"
    except (ValueError, KeyError, TypeError):
        pass
    return None


def _retry_delay(err_body, attempt):
    """Honour the API's own retry hint (RetryInfo.retryDelay, e.g. "31s"); otherwise back off exponentially."""
    try:
        for d in json.loads(err_body)["error"].get("details", []):
            if d.get("@type", "").endswith("RetryInfo"):
                return float(d["retryDelay"].rstrip("s")) + 1
    except (ValueError, KeyError, TypeError):
        pass
    return min(60.0, 2.0 * 2 ** attempt)


def call(t, key=None, retries=8):
    """One thread through Gemini; returns the cached record (prediction, usage, latency)."""
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt_for(t)}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": SCHEMA,
                             "thinkingConfig": {"thinkingLevel": THINKING}, "maxOutputTokens": 4000},
    }).encode()
    req = urllib.request.Request(API.format(model=MODEL), data=body, method="POST",
                                 headers={"x-goog-api-key": key or load_key(), "Content-Type": "application/json"})
    for attempt in range(retries):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            latency = round(time.perf_counter() - t0, 3)  # the successful attempt only, not time spent waiting to retry
            break
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            daily = e.code == 429 and _daily_quota(err)
            if daily:
                raise QuotaExhausted(f"Gemini daily quota reached for {MODEL}: {daily}. "
                                     "Enable billing on the Google AI Studio project, or wait until the quota resets.")
            if e.code in (429, 500, 503) and attempt < retries - 1:
                time.sleep(_retry_delay(err, attempt))
                continue
            try:
                msg = json.loads(err)["error"]["message"].split("\n")[0]
            except (ValueError, KeyError):
                msg = err[:300]
            raise RuntimeError(f"Gemini HTTP {e.code}: {msg}")
    cand = (resp.get("candidates") or [None])[0]
    finish = cand.get("finishReason") if cand else resp.get("promptFeedback", {}).get("blockReason", "NO_CANDIDATE")
    pred, note = REFUSED, (finish or "unknown").lower()
    if finish == "STOP":
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
        try:
            pred, note = to_pred(json.loads(text)), None
        except (ValueError, KeyError, TypeError):
            pred, note = REFUSED, "bad_json"
    elif finish == "MAX_TOKENS":
        note = "max_tokens"
    u = resp.get("usageMetadata", {})
    return {"pred": pred, "note": note, "model": resp.get("modelVersion", MODEL), "response_id": resp.get("responseId"),
            "latency_s": latency, "finish": finish,
            "usage": {"input_tokens": u.get("promptTokenCount", 0),
                      "output_tokens": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)}}


def main():
    threads = [json.loads(l) for l in open(ROOT / "data/threads.jsonl")]
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [t for t in threads if not (CACHE / f"{t['id']}.json").exists()]
    key = load_key() if todo else None

    def one(t):
        out = call(t, key=key)
        (CACHE / f"{t['id']}.json").write_text(json.dumps(out))
        return out

    t0 = time.perf_counter()
    with ThreadPoolExecutor(WORKERS) as pool:
        outs = list(pool.map(one, todo))
    wall = time.perf_counter() - t0
    if todo:
        (ROOT / "baseline/run_meta_gemini.json").write_text(json.dumps({
            "threads": len(todo), "workers": WORKERS, "wall_s": round(wall, 2), "model_id": MODEL, "thinking": THINKING,
            "price_per_mtok": PRICE, "not_answered": sum(o["note"] is not None for o in outs),
            "finished": time.strftime("%Y-%m-%d %H:%M")}))
    print(f"{len(todo)} new calls in {wall:.1f}s ({len(threads) - len(todo)} cached)")


if __name__ == "__main__":
    main()
