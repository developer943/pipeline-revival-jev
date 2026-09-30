"""The baseline prompt, used by the Gemini baseline (run_gemini.py), so it gets
the identical system prompt, state, question definitions and output schema. Jev gets the same questions (jevlib.QUESTIONS).
"""
import json

import jevlib

CLASSES = list(jevlib.QUESTIONS["category"]["criteria"])
TIMEFRAMES = list(jevlib.QUESTIONS["awaited_timeframe"]["criteria"])

SYSTEM = """You triage dead sales email threads. You receive one thread as JSON (`state`) and a set of question
definitions (`questions`). Answer every question from the thread alone, following each question's instructions and
option descriptions exactly. For `category`, give a probability for every option; the probabilities must sum to 1
and should reflect how likely each option is to be correct. For `named_trigger`, give the probability that the answer
is yes. For `trigger_clarity` and `seniority`, give the index (0-4) of the best-matching level."""

SCHEMA = {
    "type": "object",
    "properties": {
        "category_probabilities": {
            "type": "object",
            "properties": {c: {"type": "number"} for c in CLASSES},
            "required": CLASSES, "additionalProperties": False,
        },
        "named_trigger": {"type": "number"},
        "awaited_timeframe": {"type": "string", "enum": TIMEFRAMES},
        "trigger_clarity": {"type": "integer", "enum": [0, 1, 2, 3, 4]},
        "seniority": {"type": "integer", "enum": [0, 1, 2, 3, 4]},
    },
    "required": ["category_probabilities", "named_trigger", "awaited_timeframe", "trigger_clarity", "seniority"],
    "additionalProperties": False,
}
QUESTION_DEFS = {k: v for k, v in jevlib.QUESTIONS.items() if k != "seller_unanswered"}  # that one is code, not model


def prompt_for(thread):
    state = {k: thread[k] for k in ("contact_role", "last_message_sent", "messages")}
    return json.dumps({"state": state, "questions": QUESTION_DEFS}, ensure_ascii=False, indent=1)


def to_pred(data):
    probs = data["category_probabilities"]
    total = sum(max(0.0, p) for p in probs.values()) or 1.0
    probs = {c: max(0.0, p) / total for c, p in probs.items()}
    return {"choice": max(probs, key=probs.get), "probs": probs, "timeframe": data["awaited_timeframe"],
            "trigger": data["trigger_clarity"] / 4, "seniority": data["seniority"] / 4,
            "named_trigger": min(1.0, max(0.0, data["named_trigger"]))}


REFUSED = {"choice": "refused", "probs": {c: 0.25 for c in CLASSES}, "timeframe": "not_stated",
           "trigger": 0.0, "seniority": 0.0, "named_trigger": 0.0}
