"""Shared bits for the Dated, Not Dead Jev work: the §05 question set, the HTTP call,
warmth composition, and TypeSafe playground share links. Stdlib only."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
PRICE_PER_MTOK = 0.042  # input only; output tokens are free (docs.typesafe.ai/models, jev-1.13)
ROOT = Path(__file__).parent

LEVELS5 = ["none", "weak", "moderate", "strong", "very strong"]

# The §05 protocol, one request per thread. Warmth is NOT asked directly: it is composed in
# code (docs: patterns/composite-scoring). Timing ripeness is date math, which Jev 1.13 is weak
# at (model-jaggedness), so Jev only picks the timeframe the buyer named and code does the math.
QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "Classify this dead sales email thread by what the buyer's last position was.",
        "criteria": {
            "soft_deferral": "The buyer postponed rather than declined: asked to revisit later, after an event, budget cycle, or date.",
            "hard_no": "The buyer clearly declined: chose a competitor, said not a fit, asked not to be contacted, however politely worded.",
            "went_quiet": "The seller's message went unanswered; the buyer never gave a position.",
            "not_sales": "Not a sales conversation: newsletters, event invites, auto-replies, internal notices.",
        },
    },
    "named_trigger": {
        "type": "noul",
        "instructions": "Did the buyer name a specific event or condition they were waiting on before revisiting (e.g. a system going live, budget season, a hire)?",
        "criteria": {"true": "A concrete, checkable event or condition is named", "false": "No condition, or only vague timing like 'later' or 'not now'"},
    },
    "seller_unanswered": {
        # Production: derive this from mail headers in code. Kept as a Noul for the text-only benchmark.
        "type": "noul",
        "instructions": "Was the last message in the thread sent by the seller and left without a reply from the buyer?",
    },
    "trigger_clarity": {
        "type": "score",
        "instructions": "How explicit is what the buyer said they were waiting on before revisiting?",
        "criteria": [
            "Nothing: the buyer gave no reason or timing to wait for",
            "Vague timing only, like 'later' or 'not this quarter'",
            "A calendar period, like 'next quarter' or 'the new year', with no event",
            "A named event or condition, like a system rollout or budget approval",
            "A named event with when it is expected, like 'once the new system is live, early next year'",
        ],
    },
    "seniority": {
        "type": "score",
        "instructions": "How senior is the buyer-side contact in `contact_role`, as a purchase decision-maker?",
        "criteria": [
            "Unknown, or not a person at the buying company (a team inbox, an events list)",
            "Individual contributor with no budget",
            "Manager or procurement officer who shapes the purchase but does not own the budget",
            "Director or head of a function who owns a budget",
            "VP, C-level, or founder",
        ],
    },
    "awaited_timeframe": {
        "type": "choice",
        "instructions": "How far after `last_message_sent` did the buyer suggest revisiting? Judge phrases like 'the new year' or 'next quarter' relative to the month it was sent.",
        "criteria": {
            "within_3_months": "Weeks away, this quarter, or next quarter",
            "3_to_6_months": "About half a year out, or after a named near-term event",
            "6_to_12_months": "Most of a year away, or after a longer project such as a system rollout",
            "over_a_year": "More than a year out",
            "not_stated": "No timing or awaited event was given",
        },
    },
}

TIMEFRAME_MONTHS = {"within_3_months": 3, "3_to_6_months": 6, "6_to_12_months": 12, "over_a_year": 18, "not_stated": None}
WEIGHTS = {"trigger": 0.44, "seniority": 0.24, "ripeness": 0.32}  # same weights as the page demo


MONTHS = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May", "Jun": "June",
          "Jul": "July", "Aug": "August", "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"}


def state_for(thread):
    # What a mail export carries: sender and month on the last message. Elapsed time stays in code.
    mon, yy = thread["date"].replace("\u2019", "'").replace("’", "'").split(" '")
    buyer = thread.get("who", "")
    return {
        "contact_role": buyer.split(" — ")[-1] or "unknown",
        "last_message_sent": f"{MONTHS[mon]} 20{yy}",
        "messages": [{"from": "seller (me)" if thread.get("lastFromSeller") else buyer,
                      "text": thread["text"].replace(" (no reply)", "")}],
    }


def ripeness(answers, months_elapsed):
    """Has the awaited moment arrived? Code-side date math over Jev's timeframe pick."""
    expected = TIMEFRAME_MONTHS[answers["awaited_timeframe"]["choice"]]
    if expected is None:
        return max(0.15, min(1.0, months_elapsed / 20))  # no stated timing: the demo's age-only fallback
    return max(0.0, min(1.0, months_elapsed / expected))


def load_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("TYPESAFE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
    if not key:
        raise SystemExit("TYPESAFE_API_KEY is empty — add it to .env in the repo folder")
    return key


def ask(state, questions=QUESTIONS, key=None, retries=4):
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Authorization": f"Bearer {key or load_key()}", "Content-Type": "application/json"})
    for attempt in range(retries):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            out["latency_s"] = round(time.perf_counter() - t0, 3)
            return out
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and attempt < retries - 1:
                time.sleep(float(e.headers.get("retry-after") or 2 ** attempt))
                continue
            raise SystemExit(f"TypeSafe HTTP {e.code}: {e.read().decode()[:400]}")


def unit(score_answer):
    """Score answer -> 0..1 (score is a probability-weighted level index)."""
    return score_answer["score"] / (len(score_answer["legend"]) - 1)


def subscores(answers, months_elapsed):
    return {"trigger": unit(answers["trigger_clarity"]), "seniority": unit(answers["seniority"]),
            "ripeness": ripeness(answers, months_elapsed)}


def warmth(answers, months_elapsed):
    """Exact port of the page demo's composition, so its verdict thresholds (55 / 42) still apply."""
    sub = subscores(answers, months_elapsed)
    clamp = lambda x, a, b: max(a, min(b, x))
    base = sum(w * sub[k] for k, w in WEIGHTS.items())
    cat = answers["category"]["choice"]
    if cat == "soft_deferral":
        return round(clamp(base * 100 * 1.05, 10, 97))
    if cat == "went_quiet":
        return round(clamp((0.5 * sub["ripeness"] + 0.3 * sub["seniority"] + 0.2) * 100, 20, 72))
    if cat == "hard_no":
        return round(clamp(base * 100 * 0.12, 3, 16))
    return round(clamp(base * 100 * 0.06, 1, 9))


# ---- lz-string compressToEncodedURIComponent (port), for playground share links ----
_URI = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$"


def _compress(s, bits_per_char, char_of):
    if not s:
        return ""
    dic, to_create = {}, set()
    w, enlarge, dsize, nbits = "", 2, 3, 2
    out, val, pos = [], 0, 0

    def emit(value, n):
        nonlocal val, pos
        for _ in range(n):
            val = (val << 1) | (value & 1)
            if pos == bits_per_char - 1:
                pos = 0; out.append(char_of(val)); val = 0
            else:
                pos += 1
            value >>= 1

    def flush_w():
        nonlocal enlarge, nbits
        if w in to_create:
            if ord(w[0]) < 256:
                emit(0, nbits); emit(ord(w[0]), 8)
            else:
                emit(1, nbits); emit(ord(w[0]), 16)
            enlarge -= 1
            if enlarge == 0:
                enlarge = 2 ** nbits; nbits += 1
            to_create.discard(w)
        else:
            emit(dic[w], nbits)
        enlarge -= 1
        if enlarge == 0:
            enlarge = 2 ** nbits; nbits += 1

    for c in s:
        if c not in dic:
            dic[c] = dsize; dsize += 1; to_create.add(c)
        wc = w + c
        if wc in dic:
            w = wc
        else:
            flush_w()
            dic[wc] = dsize; dsize += 1
            w = c
    if w:
        flush_w()
    emit(2, nbits)
    while True:
        val <<= 1
        if pos == bits_per_char - 1:
            out.append(char_of(val)); break
        pos += 1
    return "".join(out)


def lz_uri(s):
    return _compress(s, 6, lambda v: _URI[v])


def playground_link(state, questions=QUESTIONS):
    payload = {
        "documentText": state if isinstance(state, str) else json.dumps(state, indent=2, ensure_ascii=False),
        "promptsText": json.dumps(questions, indent=2, ensure_ascii=False),
        "apiVersion": "v1",
        "selectedModels": [MODEL],
    }
    return "https://console.typesafe.ai/playground#share/" + lz_uri(json.dumps(payload, ensure_ascii=False))
