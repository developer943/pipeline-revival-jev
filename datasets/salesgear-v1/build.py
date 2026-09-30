"""Build the salesgear-v1 test set from source.py: threads.jsonl (what the models see) and labels.csv (the answer key).

    python3 datasets/salesgear-v1/build.py

The labels are fixed in source.py before any model runs. This script only derives what follows mechanically from
them (the timeframe bucket and reopen_worthy, see LABELING.md), fills in names, and shuffles the order with a fixed
seed so the file order gives no hint of the label. Re-running it produces identical files.
"""
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from source import THREADS  # noqa: E402

SEED = 20261001
AS_OF = (2026, 9)  # the month the test treats as "today"; run the app with --as-of 2026-09
SELLER = "Alex"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
SHORT = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
FIRST = ["Karen", "Tomás", "Priya", "Daniel", "Lena", "Omar", "Grace", "Aisha", "Wei", "Hannah", "Kofi", "Mei",
         "Jonas", "Fatima", "Luca", "Nadia", "Ravi", "Elena", "Sam", "Yuki", "Chloe", "Diego", "Ingrid", "Mateo",
         "Zara", "Ben", "Anika", "Owen", "Rosa", "Felix", "Ines", "Victor", "Tara", "Leo", "Gwen", "Paul", "Kim",
         "Lars", "Sofia", "Ahmed", "Maria", "Irene", "Lucas", "Rachel", "Hugo", "Amara", "Noah", "Esther"]
LAST = ["Holt", "Okafor", "Lindqvist", "Nair", "Brennan", "Vogel", "Haddad", "Park", "Silva", "Mensah", "Chen",
        "Kowalski", "Ruiz", "Tanaka", "Dubois", "Ahmed", "Moretti", "Fischer", "Patel", "Novak", "Walsh", "Reyes",
        "Adeyemi", "Sørensen", "Castillo", "Byrne", "Iyer", "Kaplan"]
COMPANIES = ["Brightwater Dental Group", "Kestrel Freight", "Juniper Health", "Orchard Lane Foods", "Tallis Energy",
             "Meridian Parts", "Blue Fern Clinics", "Arden Mills", "Copperline Logistics", "Harborview Hotels",
             "Northgate Credit Union", "Solace Home Care", "Pinecrest Schools", "Vela Robotics", "Granite Peak Insurance",
             "Castellan Foods", "Riverside Transit", "Oakmont Labs", "Silverleaf Hospitality", "Evergreen Property",
             "Beacon Payroll", "Cobalt Analytics", "Fairway Clinics", "Marlow & Finch"]
SIGS = ["\n\nBest,\n{first}", "\n\n—\n{first} {last}\n{role} | {company}", "\n\nSent from my iPhone", "\n\nThanks,\n{first}"]
CLASSES = ["soft_deferral", "hard_no", "went_quiet", "not_sales"]
# Neutral earlier context, prepended to some buyer-final threads so not every thread is a single message.
# It never carries a position, so the label still rests on the buyer's last message.
EARLIER_ME = ["Great to meet you today, {first}. Here's the recap and the proposal we discussed.",
              "Hi {first}, attaching the pricing and the security overview you asked for.",
              "Thanks for the call. As promised, here's the case study from a team about your size.",
              "Hi {first}, following up on the demo. The recording is linked below."]
EARLIER_B = ["Thanks, looping in my team.", "Got it, thanks. Reading through it now.",
             "Appreciate it. A couple of people here will want to see this.", "Thanks {me}, this is helpful."]


def ym(s):
    mon, yr = s.split()
    return int(yr), SHORT[mon]


def months_between(a, b):
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def bucket(months):
    if months is None:
        return "not_stated"
    return "within_3_months" if months <= 3 else "3_to_6_months" if months <= 6 else \
        "6_to_12_months" if months <= 12 else "over_a_year"


def check(src):
    problems = []
    seen = set()
    for i, t in enumerate(src):
        where = f"source entry {i + 1} ({t['label']}, {t['sent']})"
        key = tuple(x[1] for x in t["msgs"])
        if key in seen:
            problems.append(f"{where}: duplicate text")
        seen.add(key)
        if t["label"] not in CLASSES:
            problems.append(f"{where}: bad label")
        if t["label"] != "soft_deferral" and (t["due"] or t["brushoff"]):
            problems.append(f"{where}: due/brushoff only apply to soft deferrals")
        if t["due"] and months_between(ym(t["sent"]), ym(t["due"])) <= 0:
            problems.append(f"{where}: due month must be after the sent month")
        if months_between(ym(t["sent"]), AS_OF) < 1:
            problems.append(f"{where}: sent month must be before the as-of month")
        if t["label"] == "went_quiet" and t["msgs"][-1][0] != "me":
            problems.append(f"{where}: a went_quiet thread must end on the seller")
    return problems


def main():
    problems = check(THREADS)
    if problems:
        sys.exit("\n".join(problems))
    rng = random.Random(SEED)
    order = list(THREADS)
    rng.shuffle(order)
    threads, labels = [], []
    for n, t in enumerate(order, 1):
        tid = f"m{n:03d}"
        first, last, company = rng.choice(FIRST), rng.choice(LAST), rng.choice(COMPANIES)
        first2 = rng.choice([f for f in FIRST if f != first])
        domain = company.lower().replace("&", "and").replace(" ", "") + ".example"
        fill = dict(first=first, last=last, company=company, first2=first2, me=SELLER, role=t["role"],
                    email=f"{first.lower()}.{last.lower()}@{domain}")
        buyer = f"{first} {last} ({t['role']}, {company})" if t["role"] != "unknown" else f"{first} {last} ({company})"
        src_msgs = list(t["msgs"])
        if t["label"] in ("soft_deferral", "hard_no") and src_msgs[0][0] == "b" and rng.random() < 0.5:
            pre = [("me", rng.choice(EARLIER_ME))]
            if rng.random() < 0.4:
                pre.append(("b", rng.choice(EARLIER_B)))
                pre.append(("me", "Happy to answer anything that comes up."))
            src_msgs = pre + src_msgs
        msgs = []
        for k, (who, text) in enumerate(src_msgs):
            text = text.format(**fill)
            if who == "me":
                sender = "seller (me)"
            elif who == "b":
                sender = buyer
                last_msg = k == len(src_msgs) - 1
                if last_msg and t["label"] != "not_sales" and "> On" not in text and rng.random() < 0.35:
                    text += rng.choice(SIGS).format(**fill)
            else:
                sender = who[2:].format(**fill)
            msgs.append({"from": sender, "text": text})
        sent = ym(t["sent"])
        elapsed = months_between(sent, AS_OF)
        due = ym(t["due"]) if t["due"] else None
        wait = months_between(sent, due) if due else None
        if t["label"] != "soft_deferral" or t["brushoff"]:
            reopen = False
        elif due:
            reopen = months_between(due, AS_OF) >= 0  # the month they asked for has arrived
        else:
            reopen = elapsed >= 6  # genuine but untimed: treat as due after six months
        threads.append({"id": tid, "contact_role": t["role"], "last_message_sent": f"{MONTHS[sent[1] - 1]} {sent[0]}",
                        "messages": msgs})
        labels.append({"id": tid, "label": t["label"], "timeframe": bucket(wait) if t["label"] == "soft_deferral" else "not_stated",
                       "near_miss": t["near"], "reopen_worthy": reopen, "months_elapsed": elapsed,
                       "due": t["due"] or "", "brushoff": t["brushoff"], "note": t["note"]})
    with open(HERE / "threads.jsonl", "w", encoding="utf-8") as f:
        for th in threads:
            f.write(json.dumps(th, ensure_ascii=False) + "\n")
    with open(HERE / "labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(labels[0]))
        w.writeheader()
        w.writerows(labels)

    c = Counter(l["label"] for l in labels)
    near = Counter(l["label"] for l in labels if l["near_miss"])
    tf = Counter(l["timeframe"] for l in labels if l["label"] == "soft_deferral")
    print(f"{len(labels)} threads → {HERE.name}/threads.jsonl + labels.csv (as of {MONTHS[AS_OF[1] - 1]} {AS_OF[0]})")
    for k in CLASSES:
        print(f"  {k:14} {c[k]:4}   near-misses {near[k]}")
    print(f"  near-misses total {sum(near.values())} ({sum(near.values()) / len(labels):.0%})")
    print(f"  reopen-worthy {sum(l['reopen_worthy'] for l in labels)} · deferral timeframes {dict(tf)}")


if __name__ == "__main__":
    main()
