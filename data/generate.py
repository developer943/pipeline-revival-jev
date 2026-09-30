"""Seeded synthetic cold-pipeline corpus: ~300 email threads, four gold classes, deliberate near-misses.

Every thread is built from a template whose gold label, trigger level and awaited timeframe are known by
construction. `reopen_worthy` is the precision@10 target: a soft deferral whose stated wait has elapsed by
AS_OF (vague deferrals count as elapsed after 6 months).

    python3 -m data.generate      # writes data/threads.jsonl and data/labels.csv
"""
import csv
import json
import random
from pathlib import Path

SEED = 20260930
AS_OF = (2026, 9)  # benchmark date: Sep 2026
OUT = Path(__file__).parent
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
TF_MONTHS = {"within_3_months": 3, "3_to_6_months": 6, "6_to_12_months": 12, "over_a_year": 18, "not_stated": None}

FIRST = ["Sarah", "Marcus", "Priya", "Dan", "Lena", "Omar", "Grace", "Tomás", "Aisha", "Wei", "Hannah", "Kofi", "Mei", "Jonas",
         "Fatima", "Luca", "Nadia", "Ravi", "Elena", "Sam", "Yuki", "Chloe", "Diego", "Ingrid", "Mateo", "Zara", "Ben", "Anika"]
LAST = ["Okafor", "Lindqvist", "Nair", "Brennan", "Vogel", "Haddad", "Park", "Silva", "Mensah", "Chen", "Kowalski", "Ruiz",
        "Tanaka", "Dubois", "Ahmed", "Moretti", "Fischer", "Patel", "Novak", "Walsh"]
ROLES = ["VP Operations", "Head of Finance", "IT Manager", "RevOps Lead", "Procurement Manager", "Director of Sales",
         "Chief Operating Officer", "Operations Analyst", "Head of Logistics", "Fleet Manager", "Founder & CEO",
         "Director of IT", "Finance Business Partner", "Senior Buyer", "VP Engineering", "Customer Success Lead"]
COMPANIES = ["Northwind Freight", "Harbor & Pike", "Lumen Retail", "Castellan Foods", "Brightline Health", "Ostrava Metals",
             "Kestrel Logistics", "Juniper Home", "Tallis Energy", "Meridian Parts", "Blue Fern Clinics", "Arden Mills"]
PRODUCT = ["the routing platform", "RouteIQ", "the dispatch module", "the scheduling tool", "the pilot", "the proposal"]
SYSTEMS = ["the new ERP", "our fleet-management system", "the warehouse migration", "the Salesforce rebuild", "our new TMS",
           "the SAP cutover", "the data-warehouse move"]
PROJECTS = ["the reorg", "our Q-close audit", "the office move", "the security review", "vendor consolidation", "the acquisition integration"]
HIRES = ["new COO", "Head of Ops", "procurement lead", "new CFO", "IT director"]
COMPETITORS = ["Routefox", "Dispatchly", "Onfleet", "a competitor", "another vendor", "our incumbent provider"]
SIGS = ["", "", "\n\nSent from my phone", "\n\n—\n{first} {last}\n{role}, {company}", "\n\nBest,\n{first}", "\n\nThanks,\n{first}\n{company}"]


def months_between(y, m):
    return (AS_OF[0] - y) * 12 + (AS_OF[1] - m)


def tf_key(months):
    if months is None:
        return "not_stated"
    return "within_3_months" if months <= 3 else "3_to_6_months" if months <= 6 else "6_to_12_months" if months <= 12 else "over_a_year"


def until_january(m):
    return 13 - m if m > 1 else 12


# ---- buyer-final templates: (label, trigger_level 0-4, timeframe months or callable(sent_month) or None, near_miss, text) ----
DEFERRALS = [
    (4, lambda m: 6, False, "Thanks for walking us through {product}. We're mid-rollout on {system}, which should be live by {when6}. Let's reconnect once that's done."),
    (4, lambda m: 6, False, "This is on our radar, but nothing moves until {system} goes live, probably {when6}. Can you check back then?"),
    (4, lambda m: 3, False, "Our {hire} starts in {when3} and will own this decision. Let's pick it back up once they've settled in."),
    (4, lambda m: 12, False, "We're locked into our current contract until {when12}. Reach out a couple of months before it ends and we'll run a proper evaluation."),
    (3, lambda m: 6, False, "We need to get through {project} first. Once that's wrapped, I'd genuinely like to revisit {product}."),
    (3, lambda m: 3, False, "The budget for this sits in the next fiscal plan. Let's talk again once it's approved."),
    (3, lambda m: 12, False, "Nothing new gets approved until {system} is fully bedded in, which realistically is most of next year. Keep us in mind after that."),
    (3, lambda m: 6, True, "Unfortunately we can't do anything while {project} is running, and I'd rather not waste your time with a no-budget pilot. After it's done, this is worth another look."),
    (2, lambda m: 3, False, "Can't take on anything new this quarter. Ping me next quarter and we'll take a proper look."),
    (2, until_january, False, "We're closing out the year and can't take anything on right now. Reach out in the new year and we can pick this up."),
    (2, lambda m: 6, False, "Honestly the second half is packed. Circle back in about six months?"),
    (2, lambda m: 12, True, "Not this year, sorry. No budget left and the team is stretched. Next year, though, I'd want to see this again."),
    (1, None, False, "It's interesting, but the timing isn't right for us. Maybe reach out again later."),
    (1, None, False, "Not a priority right now, but I don't want to close the door. Check back sometime."),
    (1, None, True, "Things are hectic at the moment and I can't give this the attention it deserves. Let's reconnect when things calm down."),
]
HARD_NOS = [
    (False, "We went with {competitor}. Signed last week, so we're set for now. Thanks for the time."),
    (False, "After reviewing internally, {product} isn't a fit for how we work. Thanks anyway."),
    (False, "Please take me off your list. We won't be buying this."),
    (False, "We've decided not to pursue this. Please don't follow up."),
    (True, "Honestly we loved the demo and your team was great. We've decided not to move forward, though, and I don't see that changing."),
    (True, "We're all set on this front. If anything changes on our side we'll reach out to you."),
    (True, "No need to circle back next quarter. We've consolidated on {competitor} for the next three years."),
    (True, "I appreciate the persistence, and I know timing is always the pitch, but this is a firm no from us."),
    (True, "We ran the numbers again and the ROI just isn't there for a team our size. Good luck with it."),
]
QUIET_SELLER = [
    (False, "Following up on my note below. Did you get a chance to look at {product}? Happy to jump on a quick call whenever works."),
    (False, "Just checking in on this. Any thoughts on the pricing I sent over?"),
    (False, "Bumping this to the top of your inbox. Would a 15-minute call next week be useful?"),
    (True, "No pressure at all. Happy to revisit next quarter if the timing is better on your side. Just let me know."),
    (True, "I know you mentioned budget season is coming up. I can hold the pilot pricing until the end of the quarter if that helps."),
]
QUIET_BUYER_OPENERS = [
    "This looks promising. Can you send over pricing for about 40 vehicles?",
    "Thanks for the demo today. Let's set up a call with my team next week.",
    "Interesting. Send me a one-pager and I'll share it internally.",
    "Could you put together a proposal? We'd want to start small.",
]
NOT_SALES = [
    (False, "Events team", "You're invited to our Q4 webinar on logistics automation. Register here. Seats are limited."),
    (False, "Newsletter", "This month in fleet ops: five trends reshaping last-mile delivery. Read the full issue on our blog."),
    (False, "Billing", "Your invoice #{inv} for {mon} is attached. Payment is due in 30 days."),
    (False, "People team", "Reminder: the all-hands moves to Thursday at 10am. Agenda to follow."),
    (False, "Recruiting", "Hi, I came across your profile and think you'd be a great fit for a senior account executive role."),
    (True, "{first} {last}", "I'm out of the office until {when3} with limited access to email. I'll reply when I'm back. For urgent matters contact the front desk."),
    (True, "{first} {last}", "Thanks for your message. I'm on parental leave until the new year and won't be checking email. I'll get back to you then."),
    (True, "Calendar", "Invitation: Quarterly business review. Rescheduled to next quarter by the organizer."),
    (True, "System", "Your free trial ends in 3 days. Upgrade now to keep your dashboards and revisit your saved reports any time."),
]
EARLIER_BUYER = ["Thanks, the demo was helpful. Looping in my team.", "Can you send the security questionnaire?",
                 "We're comparing a few options right now.", "Pricing looks reasonable. A few questions on the contract terms."]
EARLIER_SELLER = ["Great to meet you today. Here's the recap and the proposal we discussed.",
                  "Attached is the pricing for the 40-vehicle tier, plus the security docs.",
                  "Following up with the case study I mentioned."]


def future_month(y, m, add):
    t = y * 12 + (m - 1) + add
    return f"{MONTHS[t % 12]} {t // 12}"


def build(rng, idx, label, spec):
    first, last = rng.choice(FIRST), rng.choice(LAST)
    role, company = rng.choice(ROLES), rng.choice(COMPANIES)
    buyer = f"{first} {last} ({role}, {company})"
    # deferrals need both ripe and not-yet-ripe cases, so spread dates across Sep 2024 – Aug 2026
    offset = rng.randint(1, 24)
    t = AS_OF[0] * 12 + (AS_OF[1] - 1) - offset
    y, m = t // 12, t % 12 + 1
    fill = dict(product=rng.choice(PRODUCT), system=rng.choice(SYSTEMS), project=rng.choice(PROJECTS), hire=rng.choice(HIRES),
                competitor=rng.choice(COMPETITORS), first=first, last=last, role=role, company=company,
                when3=future_month(y, m, 3).split()[0], when6=future_month(y, m, 6), when12=future_month(y, m, 12),
                inv=rng.randint(10000, 99999), mon=MONTHS[m - 1])
    sig = rng.choice(SIGS).format(**fill)
    sent = f"{MONTHS[m - 1]} {y}"
    earlier = []
    if rng.random() < 0.55:
        earlier.append({"from": "seller (me)", "text": rng.choice(EARLIER_SELLER)})
        if rng.random() < 0.5:
            earlier.append({"from": buyer, "text": rng.choice(EARLIER_BUYER)})
    gold = {"id": f"t{idx:03d}", "label": label, "trigger_level": 0, "timeframe": "not_stated", "near_miss": spec[-2] if label != "not_sales" else spec[0],
            "months_elapsed": offset, "last_from_seller": False, "contact_role": role}
    if label == "soft_deferral":
        level, tf, near, text = spec
        months = tf(m) if tf else None
        gold.update(trigger_level=level, timeframe=tf_key(months),
                    reopen_worthy=offset >= (months if months else 6))
        msgs = earlier + [{"from": buyer, "text": text.format(**fill) + sig}]
    elif label == "hard_no":
        near, text = spec
        msgs = earlier + [{"from": buyer, "text": text.format(**fill) + sig}]
    elif label == "went_quiet":
        near, text = spec
        opener = {"from": buyer, "text": rng.choice(QUIET_BUYER_OPENERS)}
        msgs = [opener, {"from": "seller (me)", "text": rng.choice(EARLIER_SELLER)}, {"from": "seller (me)", "text": text.format(**fill)}]
        if rng.random() < 0.4:
            msgs.insert(2, {"from": "seller (me)", "text": "Just checking this landed okay."})
        gold["last_from_seller"] = True
    else:
        near, sender, text = spec
        sender = sender.format(**fill)
        msgs = [{"from": sender, "text": text.format(**fill)}]
        role = "unknown" if sender in ("Events team", "Newsletter", "Billing", "People team", "Recruiting", "Calendar", "System") else role
        gold["contact_role"] = role
    gold.setdefault("reopen_worthy", False)
    thread = {"id": gold["id"], "contact_role": gold["contact_role"], "last_message_sent": sent, "messages": msgs}
    return thread, gold


def main():
    rng = random.Random(SEED)
    plan = [("soft_deferral", DEFERRALS, 90), ("hard_no", HARD_NOS, 75), ("went_quiet", QUIET_SELLER, 75), ("not_sales", NOT_SALES, 60)]
    items = []
    for label, pool, n in plan:
        for k in range(n):
            items.append((label, pool[k % len(pool)]))  # cycle templates so each is used evenly
    rng.shuffle(items)
    threads, golds = [], []
    for i, (label, spec) in enumerate(items):
        th, g = build(rng, i, label, spec)
        threads.append(th)
        golds.append(g)
    with open(OUT / "threads.jsonl", "w") as f:
        for th in threads:
            f.write(json.dumps(th, ensure_ascii=False) + "\n")
    with open(OUT / "labels.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(golds[0]))
        w.writeheader()
        w.writerows(golds)
    from collections import Counter
    print(len(threads), "threads", dict(Counter(g["label"] for g in golds)),
          "near-misses:", sum(g["near_miss"] for g in golds), "reopen-worthy:", sum(g["reopen_worthy"] for g in golds))


if __name__ == "__main__":
    main()
