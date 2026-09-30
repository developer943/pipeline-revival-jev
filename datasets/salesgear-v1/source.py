"""Hand-written threads for the salesgear-v1 test set. build.py turns these into threads.jsonl + labels.csv.

Each entry is T(label, sent, role, msgs, due=..., near=..., brushoff=..., note=...):
  sent      month of the thread's last message, e.g. "Jan 2026"
  due       soft deferrals only: the month the buyer asked you to come back (None = no timing given)
  near      a near-miss: wording that looks like another category
  brushoff  a deferral that invites you back but signals low interest (never reopen-worthy)
  msgs      ("me", text) is the seller, ("b", text) the buyer, ("x:Sender", text) anyone else

Placeholders filled by build.py: {first} buyer's first name, {me} seller's first name, {company} buyer's company,
{first2} a colleague's first name, {email} an address at the buyer's domain.

The seller sells one of four fictional products: an AP-automation tool (finance buyers), a shift-scheduling tool
(operations/HR), a security-awareness platform (IT/security) and a customer-support platform (CX).
"""


def T(label, sent, role, msgs, due=None, near=False, brushoff=False, note=""):
    return dict(label=label, sent=sent, role=role, msgs=msgs, due=due, near=near, brushoff=brushoff, note=note)


D, H, Q, N = "soft_deferral", "hard_no", "went_quiet", "not_sales"

THREADS = [
    # ------------------------------------------------------------------ soft deferrals: named event + timing
    T(D, "Jan 2026", "VP Finance", due="Jul 2026", msgs=[
        ("me", "Thanks for the time on Tuesday, {first}. Recap and pricing for the three-entity setup are attached."),
        ("b", "Thanks, this is genuinely useful. Problem is we're in the middle of moving to NetSuite and my team can't absorb a second rollout. Go-live is set for June. Can you come back to me in July once the dust settles?")]),
    T(D, "Oct 2025", "Director of Operations", due="Mar 2026", msgs=[
        ("b", "We liked the demo. Honestly the blocker is our union contract renegotiation. Anything that touches scheduling rules has to wait until the new agreement is signed, which should be around March. Let's talk after that.")]),
    T(D, "May 2026", "CISO", due="Jan 2027", msgs=[
        ("me", "Hi {first}, following up on the phishing-simulation pilot we discussed."),
        ("b", "Appreciate the follow-up. We're heads-down on our SOC 2 Type II audit through the end of the year. Put a pin in it and reach out in January.")]),
    T(D, "Aug 2025", "Head of Customer Support", due="Jun 2026", msgs=[
        ("b", "Can you send the migration plan?"),
        ("me", "Attached, plus the Zendesk import checklist."),
        ("b", "Thank you. We're renewing Zendesk for one more year (the contract auto-renewed before I could stop it, long story). Mark your calendar for next June. That's when I can actually make a switch.")]),
    T(D, "Mar 2026", "CFO", due="Jun 2026", msgs=[
        ("b", "Not before our new controller starts. She's joining in May and I want her to own the AP process from day one. Ping me in June.")]),
    T(D, "Nov 2025", "COO", due="Apr 2026", msgs=[
        ("me", "Hi {first}, here's the rollout plan for your five sites."),
        ("b", "We're opening two new sites in Q1 and I don't want to change the scheduling tool mid-launch. Once both sites are up, say April, I'd be happy to revisit.")]),
    T(D, "Jul 2026", "IT Director", due="Oct 2026", msgs=[
        ("b", "The earliest I can get this into budget is the FY27 planning cycle, which kicks off in October. Reach out in early October and I'll put it in front of the committee.")]),
    T(D, "Feb 2025", "VP People", due="Sep 2025", msgs=[
        ("b", "We're in the middle of an acquisition and everything touching headcount is frozen until the deal closes. Lawyers say Q3. Can we reconnect in September?")]),
    T(D, "Dec 2025", "Head of Support Operations", due="Jan 2026", msgs=[
        ("b", "Can't look at this until after the holidays. Try me mid-January.")]),
    T(D, "Sep 2025", "Procurement Manager", due="Apr 2026", msgs=[
        ("me", "Hi {first}, is there anything else procurement needs from us?"),
        ("b", "Our vendor onboarding freeze runs until the end of our fiscal year (March 31). After that I can start the supplier review. Please resend the security pack in April.")]),
    T(D, "Apr 2026", "Chief Nursing Officer", due="Dec 2026", msgs=[
        ("b", "Our EHR upgrade goes live in November and every nurse manager is buried in training until then. After November I'd like to see this again.")]),
    T(D, "Jun 2025", "Security Engineering Manager", due="Aug 2025", near=True, note="lower-case, casual", msgs=[
        ("b", "yeah this is good but we literally just hired a new head of security, starts in 2 weeks. i don't want to buy anything he hasn't seen. circle back in a couple months?")]),
    T(D, "Jan 2025", "VP Customer Experience", due="Jul 2025", msgs=[
        ("b", "We're consolidating three support teams into one this year. Until the org design is final (target: end of Q2) I can't commit to a platform. Reconnect in July?")]),
    T(D, "Mar 2026", "Finance Director", due="May 2026", msgs=[
        ("b", "Thank you for the offer. At the moment we are finishing the year-end closing and the auditors are with us until end of April. Please contact me again in May, then we have time to discuss properly.")]),
    T(D, "Aug 2026", "Head of Workforce Management", due="Feb 2027", msgs=[
        ("b", "Peak season starts next week and runs through January. No way we change tools before February. Talk then.")]),
    T(D, "Oct 2024", "Director of IT", due="Oct 2025", msgs=[
        ("b", "We're migrating from on-prem Exchange to Microsoft 365 over the next year. Phishing training makes sense after that, not before. Let's revisit next October.")]),
    T(D, "Oct 2024", "VP Sales Operations", due="Apr 2025", msgs=[
        ("b", "Our CRM migration is done in March. After that I can finally look at tooling around it. April works.")]),
    T(D, "Jun 2026", "COO", due="Apr 2027", msgs=[
        ("b", "We've signed a 12-month extension with our current provider that ends next June. Reach out in April 2027 and we'll run a proper RFP.")]),
    T(D, "Aug 2026", "Head of Finance", due="Nov 2026", msgs=[
        ("b", "Budget season kicks off in November. Send me something in early November and I'll include it in the proposal.")]),
    T(D, "Jul 2026", "Security Awareness Lead", due="Dec 2026", msgs=[
        ("b", "Our current training contract runs until the end of the year. Talk in December?")]),
    T(D, "Mar 2026", "Director of Customer Operations", due="Feb 2027", msgs=[
        ("b", "We're moving to a new phone system and the cutover is planned for early 2027. I'd rather do support tooling after that. Early 2027 then.")]),
    T(D, "Sep 2024", "VP Workforce", due="Jan 2026", msgs=[
        ("b", "Nothing until 2026, sorry. We're in a two-year cost freeze.")]),
    T(D, "Apr 2025", "Group Financial Controller", due="Apr 2026", msgs=[
        ("b", "We're in the middle of an ERP selection that won't conclude until next spring. AP automation depends on what we pick. Reach out in about a year.")]),
    T(D, "Jan 2025", "Head of Service Desk", due="Jul 2026", msgs=[
        ("b", "Two years left on our current contract, and early termination is painful. Let's talk about six months before it ends, so mid-2026.")]),
    T(D, "Dec 2025", "Director of HR Operations", due="Oct 2026", msgs=[
        ("b", "We're implementing Workday in 2026 and scheduling has to integrate with it. Our SI says integrations open up in Q4. Reach out in October.")]),
    T(D, "Jun 2025", "IT Director", due="Oct 2025", msgs=[
        ("b", "We're evaluating you alongside two others, but the evaluation itself is on hold until our new CIO starts in September. She'll restart it. Please reach out in October.")]),
    T(D, "Nov 2025", "Finance Director", due="Mar 2026", near=True, note="formal, non-native English", msgs=[
        ("b", "Dear {me}, thank you for your proposal. Unfortunately, for this moment we must postpone, because of the reorganisation of our finance department which is planned until February. We would be happy if you contact us again in March 2026. Kind regards")]),
    T(D, "Aug 2025", "Customer Support Manager", due="Jan 2026", msgs=[
        ("b", "I'd love to but my director just froze spending for the rest of the year. Let's talk in January.")]),
    T(D, "May 2026", "Head of Compliance", due="Sep 2026", msgs=[
        ("b", "We need legal to finish the new data processing policy first. They said 'a few months'. Let's regroup after the summer.")]),
    T(D, "Feb 2025", "Executive Assistant to the CEO", due="May 2025", near=True, note="written by an assistant on the buyer's behalf", msgs=[
        ("b", "Hi {me}, I'm responding on behalf of {first2}. She asked me to let you know she's interested but can't take meetings until after the product launch at the end of April. Could you reach out again in May?")]),

    # ------------------------------------------------------------------ soft deferrals: long or messy, deferral buried
    T(D, "Jan 2026", "CFO", due="Apr 2026", near=True, note="objections first, deferral at the end", msgs=[
        ("me", "Hi {first}, the full proposal is attached, including the three-entity pricing."),
        ("b", "Thanks for the detailed proposal. A few thoughts: (1) the per-entity pricing is higher than what we pay today, (2) our auditors will want to see your SOC 1 report, and (3) I'd need IT to sign off on the SSO setup. None of that is a dealbreaker, but none of it happens before our fiscal year-end in March. If you can send the SOC 1 and sharpen the pricing, let's reconvene in April.")]),
    T(D, "Sep 2025", "Director of Operations", due="Feb 2026", near=True, note="quoted seller text below the reply", msgs=[
        ("b", "Hi {me},\n\nSorry for the slow reply, it's been a month. Short version: we're pausing all new tooling until our new VP Ops is hired (search is ongoing, hoping for Dec/Jan). They'll want a say. Reach out in Feb and I'll intro you.\n\n{first}\n\n> On Aug 12, {me} wrote:\n> Hi {first}, any thoughts on the pilot proposal?")]),
    T(D, "Mar 2026", "Head of IT", due="Sep 2026", msgs=[
        ("b", "We did a quick internal review. The team prefers your product over the other two we looked at, but security won't approve any new vendor until our pen-test remediation is done. Rough ETA is Q3. Let's touch base in September.")]),
    T(D, "Nov 2024", "VP Customer Support", due="Jun 2025", msgs=[
        ("b", "Decision is on hold. Our parent company is rolling out a group-wide CRM in 2025 and we may be forced onto their support tool. Once we know (probably mid-2025) I'll know whether we can pick our own. Check in around June?")]),
    T(D, "Apr 2026", "VP Operations", due="Jul 2026", near=True, note="conditional on a competitor pilot; seller replied last", msgs=[
        ("b", "We're doing a pilot with another vendor through June. If it doesn't work out, you're next. Try me in July."),
        ("me", "Fair enough, hope it goes well (but not too well). I'll check in early July.")]),
    T(D, "Oct 2025", "Head of Support", due="Jan 2026", near=True, note="two-word reply", msgs=[
        ("me", "Hi {first}, would a 20-minute walkthrough next week be useful?"),
        ("b", "lol no bandwidth. Q1.")]),

    # ------------------------------------------------------------------ soft deferrals the seller acknowledged (seller spoke last)
    T(D, "May 2025", "Head of Support", due="Aug 2025", near=True, note="buyer deferred; seller's reply is the last message", msgs=[
        ("b", "Love it but we're mid hiring spree: 12 new agents starting in June. After onboarding wraps in August, let's pick this up."),
        ("me", "Makes sense, I'll put a note in for August. Enjoy the new team!")]),
    T(D, "Nov 2024", "Controller", due="Apr 2025", near=True, note="buyer deferred; seller's reply is the last message", msgs=[
        ("b", "We're switching banks in Q1 and I'd rather not integrate twice. Reach back out in April."),
        ("me", "Will do, {first}. Talk in April.")]),
    T(D, "Feb 2026", "Operations Manager", due="Apr 2026", near=True, note="buyer deferred; seller's reply is the last message", msgs=[
        ("b", "We're waiting on the board to approve the expansion budget, which happens at the March board meeting. If it passes I'll have money for this in Q2."),
        ("me", "Great, fingers crossed for March. I'll check in once the board has met.")]),
    T(D, "Jun 2026", "Director of Finance", due="Sep 2026", near=True, note="buyer deferred; seller's reply is the last message", msgs=[
        ("me", "Hi {first}, attaching the updated pricing we discussed."),
        ("b", "Thanks. Our CFO wants to see Q2 numbers before approving anything new. Those land in August. Check back in September."),
        ("me", "Perfect, September it is.")]),

    # ------------------------------------------------------------------ soft deferrals: calendar timing only
    T(D, "Sep 2025", "Head of Finance Operations", due="Jan 2026", msgs=[
        ("b", "Q4 is all hands on deck for close. Let's pick up in the new year.")]),
    T(D, "Jun 2026", "HR Director", due="Sep 2026", msgs=[
        ("b", "Summer is a write-off for us, half the team is out. September?")]),
    T(D, "Mar 2025", "Customer Care Manager", due="Apr 2025", msgs=[
        ("b", "Next quarter, ok? This one is spoken for.")]),
    T(D, "Dec 2024", "IT Manager", due="Jul 2025", msgs=[
        ("b", "Let's revisit in the second half of next year.")]),
    T(D, "Apr 2026", "VP Finance", due="Jul 2026", msgs=[
        ("b", "Not this fiscal. Our FY starts in July. Reach out then and we'll look at it with the new budget.")]),
    T(D, "Jan 2026", "Director of Nursing Operations", due="Sep 2026", msgs=[
        ("me", "Hi {first}, checking whether spring is still a busy time for your team."),
        ("b", "Spring is chaos. Let's aim for September.")]),
    T(D, "Aug 2025", "Support Team Lead", due="Dec 2025", msgs=[
        ("b", "After Black Friday. Seriously, nothing before December.")]),
    T(D, "Oct 2025", "Head of Security", due="Jan 2026", msgs=[
        ("b", "Early 2026 would be better for us.")]),
    T(D, "May 2026", "CFO", due="Nov 2026", msgs=[
        ("b", "Circle back in about six months.")]),
    T(D, "Feb 2026", "Workforce Planning Lead", due="Apr 2026", msgs=[
        ("b", "Ping me after Easter.")]),

    # ------------------------------------------------------------------ soft deferrals: genuine, no timing given
    T(D, "Mar 2025", "VP Operations", msgs=[
        ("b", "I like it, genuinely, but I can't prioritise it right now. Keep me posted on new features and let's talk again down the line.")]),
    T(D, "Nov 2025", "IT Security Lead", msgs=[
        ("b", "Not right now, too much on the plate. Don't be a stranger though.")]),
    T(D, "Jul 2026", "Customer Success Director", msgs=[
        ("b", "Timing isn't right. Let's reconnect later.")]),
    T(D, "Jan 2026", "Finance Manager", msgs=[
        ("b", "We're not ready for this yet, but I can see us needing it once we grow. Check back sometime.")]),
    T(D, "Sep 2024", "Head of People Operations", msgs=[
        ("b", "Interesting, but it's not the right moment. Happy to chat again when things calm down.")]),
    T(D, "Apr 2026", "Director of Support", msgs=[
        ("b", "We'll get there, just not yet. Keep in touch.")]),

    # ------------------------------------------------------------------ soft deferrals that are really brush-offs (never reopen-worthy)
    T(D, "Jun 2025", "VP Finance", due="Jun 2026", near=True, brushoff=True, note="invites a check-back but says it isn't on their list", msgs=[
        ("b", "Maybe someday. Honestly it's not something we're looking at, but feel free to check back in a year or so.")]),
    T(D, "Oct 2025", "Head of CX", due="Jan 2026", near=True, brushoff=True, note="happy with current tool", msgs=[
        ("b", "We're pretty happy with what we have, to be honest. Maybe reach out next year and see if anything's changed?")]),
    T(D, "Feb 2026", "Controller", due="Aug 2026", near=True, brushoff=True, note="low on the list", msgs=[
        ("b", "Sure, try again in 6 months. Can't promise anything, this is low on the list.")]),
    T(D, "May 2025", "Director of IT", due="Apr 2026", near=True, brushoff=True, note="just renewed a competitor for two years", msgs=[
        ("b", "Put me down for a check-in next spring I guess. We just renewed with our current vendor for 2 years though.")]),
    T(D, "Aug 2025", "VP Support", due="Jan 2026", near=True, brushoff=True, note="'probably not'", msgs=[
        ("b", "Honestly? Probably not. But ping me in Q1 and I'll give you a straight answer.")]),

    # ------------------------------------------------------------------ hard no: plain
    T(H, "Jan 2026", "VP Finance", msgs=[("b", "We went with Ledgerly. Contract signed last week. Thanks for your time.")]),
    T(H, "Mar 2025", "IT Director", msgs=[("b", "Please remove me from your mailing list.")]),
    T(H, "Sep 2025", "Head of Support", msgs=[("b", "We've decided to stay with our current platform. Please don't follow up.")]),
    T(H, "Jun 2026", "COO", msgs=[("b", "Not a fit for us. Best of luck.")]),
    T(H, "Nov 2024", "CISO", msgs=[("b", "We built our own phishing simulation in-house last year, so we won't need an external tool.")]),
    T(H, "Feb 2026", "HR Director", msgs=[("b", "Thanks, but we're not interested.")]),
    T(H, "Aug 2025", "Controller", msgs=[("b", "We chose a different vendor after the RFP. Appreciate your effort throughout the process.")]),
    T(H, "Apr 2026", "Support Operations Lead", msgs=[
        ("me", "Hi {first}, pricing for 60 agents is attached."),
        ("b", "The pricing is roughly double our budget and there's no scenario where that changes. We'll pass.")]),
    T(H, "Dec 2025", "Director of IT", msgs=[("b", "This one's a no. We're standardising on Microsoft's built-in tools.")]),
    T(H, "Jul 2025", "Operations Director", msgs=[("b", "We've signed a three-year deal with Rosterly. Not looking at alternatives.")]),
    T(H, "May 2025", "Finance Manager", msgs=[("b", "We're a 12-person company, this is way more than we need. Thanks though.")]),
    T(H, "Oct 2025", "VP Customer Experience", msgs=[("b", "We've decided against moving support platforms at all. Our current tool is fine.")]),
    T(H, "Mar 2026", "Security Manager", msgs=[("b", "Our procurement team rejected the vendor assessment. The data residency requirements can't be met, so we're closing this out on our side.")]),
    T(H, "Jan 2025", "Head of People", msgs=[("b", "Stop emailing me please.")]),
    T(H, "Sep 2024", "CFO", msgs=[("b", "After much discussion we're not moving forward. The board wants to reduce vendor count, not add to it.")]),
    T(H, "Aug 2025", "Procurement Lead", msgs=[
        ("me", "Hi {first}, attaching the revised MSA with the changes your legal team requested."),
        ("b", "Thanks {me}. Legal reviewed it and we can't accept the liability cap. We're ending the process here.")]),
    T(H, "Apr 2026", "VP Operations", msgs=[
        ("b", "Can you do a pilot at one site?"),
        ("me", "Absolutely, here's the pilot plan."),
        ("b", "Pilot plan looks fine, but corporate just mandated a single vendor across all regions, and it's not you. Sorry.")]),
    T(H, "Dec 2025", "CFO", msgs=[("b", "Unsubscribe.")]),
    T(H, "Oct 2025", "Security Operations Lead", msgs=[("b", "We're a government contractor and you're not FedRAMP authorised. That's a hard requirement, so we can't move forward.")]),
    T(H, "Jul 2025", "Support Director", msgs=[("b", "We just got acquired and the parent company has its own support stack. This project is dead, unfortunately.")]),
    T(H, "Mar 2025", "Director of Finance", msgs=[("b", "We've decided to automate AP with our ERP's native module instead. Thanks for the demos.")]),
    T(H, "Jan 2026", "VP IT", msgs=[("b", "I passed this to our security team and they've said no. Not a priority now or in the future.")]),
    T(H, "May 2025", "Head of Scheduling", msgs=[("b", "We tested the trial and it didn't fit how our shifts work (rotating 12s). It's a no from us.")]),
    T(H, "Sep 2025", "Head of Customer Support", msgs=[("b", "Thanks for the persistence, but please stop reaching out. We're happy with our setup.")]),
    T(H, "Nov 2024", "IT Operations Manager", msgs=[("b", "Not a fit for our environment, we're a Linux shop.")]),
    T(H, "Aug 2025", "COO", msgs=[("b", "Decided to stay manual. It's working and the team doesn't want another tool.")]),
    T(H, "Apr 2025", "VP Support", msgs=[("b", "We're going with DeskHarbor. The decision was made above my head, sorry.")]),
    T(H, "Oct 2025", "Finance Operations Manager", msgs=[("b", "We already use a spend tool bundled with our corporate cards, so there's no case for a second one.")]),
    T(H, "Jan 2025", "Director of Security", msgs=[("b", "We are not in the market for this. Please remove us from your sequence.")]),
    T(H, "Mar 2026", "VP Finance", msgs=[("b", "Another vendor offered us a 3-year price lock and we took it. Can't justify switching.")]),
    T(H, "Dec 2025", "Customer Support Lead", msgs=[("b", "I'm not the decision maker, but I asked and the answer from my VP is no.")]),
    T(H, "Sep 2025", "VP Finance", msgs=[("b", "The team voted and we're going with Ledgerly. It was close, if that's any consolation. Good luck out there.")]),
    T(H, "Nov 2025", "Head of Service Delivery", msgs=[("b", "We will not be proceeding. Thank you.")]),

    # ------------------------------------------------------------------ hard no that sounds soft (near-misses)
    T(H, "Feb 2025", "VP Operations", near=True, note="warm tone, firm no", msgs=[
        ("b", "Honestly the demo was great and your team was lovely. We've decided not to go ahead, though, and I don't see that changing. Wishing you all the best.")]),
    T(H, "Jun 2025", "Head of IT", near=True, note="'we'll reach out', no invitation back", msgs=[
        ("b", "We're all set on this front. If anything changes on our side we'll reach out to you.")]),
    T(H, "Nov 2025", "Director of Support", near=True, note="uses 'circle back next quarter' to refuse", msgs=[
        ("b", "No need to circle back next quarter. We've consolidated on Zendesk for the next three years.")]),
    T(H, "Aug 2026", "Finance Director", near=True, note="refuses the timing framing", msgs=[
        ("b", "I know timing is usually the pitch, but it's not a timing thing. It's a no.")]),
    T(H, "Apr 2025", "VP People", near=True, note="'stay in touch', but built in-house", msgs=[
        ("b", "Let's stay in touch on LinkedIn, but we won't be buying a scheduling tool. We just finished building one into our HRIS.")]),
    T(H, "Dec 2024", "Head of Security", near=True, note="'maybe in another life'", msgs=[
        ("b", "Maybe in another life! We're committed to PhishGuard for the foreseeable future.")]),
    T(H, "Jul 2026", "COO", near=True, note="reply to a check-back", msgs=[
        ("me", "Hi {first}, you mentioned revisiting this in the summer. Is now a better time?"),
        ("b", "Appreciate you checking back in. We've looked again and the answer is still no. Please close our file.")]),
    T(H, "Oct 2024", "Controller", near=True, note="quotes 'revisit' to refuse it", msgs=[
        ("b", "Revisit? No, I'm afraid we made our decision. Thanks for being so patient with us.")]),
    T(H, "Mar 2026", "IT Manager", near=True, note="requirement the product will never meet", msgs=[
        ("b", "We'd need this to support on-prem deployment and I know that's not on your roadmap. So realistically this isn't going to work for us.")]),
    T(H, "Jan 2026", "Director of Workforce", near=True, note="mentions a future date, but to rule it out", msgs=[
        ("b", "Thanks for following up. We ended up renewing with our incumbent for another two years, and after that we'll likely build internally. I'd take us off your list.")]),
    T(H, "May 2026", "Head of CX", near=True, note="'not now, not later'", msgs=[
        ("b", "Not now, not later. Sorry to be blunt! We just don't have the use case.")]),
    T(H, "Feb 2026", "Chief Information Officer", near=True, note="'this year or next' reads like timing", msgs=[
        ("b", "We have decided to discontinue the evaluation. Our priorities have shifted to AI initiatives and there is no budget for security awareness this year or next.")]),
    T(H, "Jun 2025", "HR Manager", near=True, note="permanent stop", msgs=[
        ("b", "Please don't take this personally, but leadership has asked me to stop all vendor conversations for this category. Permanently.")]),
    T(H, "Feb 2026", "Finance Director", near=True, note="quoted seller 'circling back' below a no", msgs=[
        ("b", "Hi {me}, sorry, I should have closed the loop sooner. We went a different direction. All the best.\n\n> On Jan 20, {me} wrote:\n> Hi {first}, circling back on the proposal. Would next week work for a call?")]),
    T(H, "Jun 2026", "People Operations Director", near=True, note="'hold off indefinitely'", msgs=[
        ("b", "We're going to hold off indefinitely. Honestly, I don't expect this to come back.")]),
    T(H, "Jul 2026", "Head of Workforce Planning", near=True, note="answers a timing question with a no", msgs=[
        ("me", "Hi {first}, checking whether Q3 is a better time to reconnect?"),
        ("b", "It isn't, and Q4 won't be either. We've decided to stay with what we have. Thanks for understanding.")]),
    T(H, "May 2026", "IT Director", near=True, note="budget cut, stated as final", msgs=[
        ("b", "Budget got cut and this project was the first to go. It won't be coming back.")]),

    # ------------------------------------------------------------------ went quiet: buyer engaged, then silence
    T(Q, "Mar 2026", "VP Finance", msgs=[
        ("b", "Can you send pricing for three entities?"),
        ("me", "Here you go. Pricing is attached and valid through April."),
        ("me", "Hi {first}, did the pricing land okay?")]),
    T(Q, "Jan 2026", "IT Manager", msgs=[
        ("b", "Thanks for the demo, looping in my manager."),
        ("me", "Great, happy to run a second session for her. Does Thursday work?")]),
    T(Q, "Nov 2025", "COO", msgs=[
        ("b", "Send me a one-pager and I'll share it with the leadership team."),
        ("me", "Attached. Happy to answer anything.")]),
    T(Q, "Aug 2025", "Operations Director", msgs=[
        ("b", "Interesting. What does implementation usually take?"),
        ("me", "Typically 4 to 6 weeks. Here's a sample plan."),
        ("me", "Hi {first}, just checking this reached you.")]),
    T(Q, "Apr 2026", "Head of Customer Support", msgs=[
        ("b", "Could you put together a proposal for 200 seats? We'd want to start in one region."),
        ("me", "Proposal attached, including the regional pilot option you mentioned."),
        ("me", "Hi {first}, wanted to make sure this didn't get lost. Any feedback?")]),
    T(Q, "Feb 2026", "Security Manager", msgs=[
        ("b", "Demo was great. Can you send the security questionnaire responses?"),
        ("me", "Attached. Let me know if your team needs anything else.")]),
    T(Q, "Apr 2025", "Director of Operations", msgs=[
        ("b", "This looks promising. Can you send over pricing for about 40 locations?"),
        ("me", "Pricing attached. The 40+ tier includes onboarding."),
        ("me", "Hi {first}, did you get a chance to look?")]),
    T(Q, "Dec 2024", "Chief Nursing Officer", msgs=[
        ("b", "Who else in healthcare uses this?"),
        ("me", "Three regional hospital groups. Happy to set up a reference call."),
        ("me", "Would a reference call next week be useful?")]),
    T(Q, "Mar 2026", "Controller", msgs=[
        ("b", "Ok, send the contract over."),
        ("me", "Contract attached. Let me know if legal has redlines."),
        ("me", "Hi {first}, checking whether legal had a chance to review.")]),
    T(Q, "Feb 2025", "Finance Director", msgs=[
        ("b", "Looks good. What's the minimum contract length?"),
        ("me", "12 months, with a 90-day out clause for the first year."),
        ("me", "Any other questions I can answer?")]),
    T(Q, "Dec 2025", "Director of IT", msgs=[
        ("b", "Let me check with IT security on the SSO piece."),
        ("me", "Of course. Here's our SSO documentation to make it easier."),
        ("me", "Hi {first}, did security have any questions?")]),
    T(Q, "Jun 2025", "Finance Manager", msgs=[
        ("b", "Can you send a quote in EUR?"),
        ("me", "Quote in EUR attached.")]),
    T(Q, "Jan 2026", "VP Customer Experience", msgs=[
        ("b", "We're interested. Who would be our point of contact during onboarding?"),
        ("me", "That would be Marta, our onboarding lead. I've cc'd her here."),
        ("me", "Hi {first}, Marta and I are ready whenever you are.")]),
    T(Q, "Oct 2025", "Procurement Manager", msgs=[
        ("b", "Sending this to procurement."),
        ("me", "Great, here's the vendor form pre-filled to save them time.")]),
    T(Q, "Feb 2026", "Head of Support", msgs=[
        ("b", "Intrigued. Can you show us the reporting side?"),
        ("me", "Absolutely. Here are three times that work for a reporting deep-dive."),
        ("me", "Hi {first}, do any of those times work?")]),
    T(Q, "Aug 2026", "COO", msgs=[
        ("b", "Can you hold the pilot pricing for us?"),
        ("me", "Yes, I can hold it through October.")]),
    T(Q, "Sep 2025", "Workforce Planning Lead", msgs=[
        ("b", "What's the earliest start date?"),
        ("me", "We could kick off as early as October 6."),
        ("me", "Should I pencil in October 6?")]),
    T(Q, "Mar 2026", "VP Operations", msgs=[
        ("b", "Great call today. Please send the recap."),
        ("me", "Recap and next steps attached."),
        ("me", "Hi {first}, any thoughts on the next steps?")]),
    T(Q, "May 2026", "Director of Finance", msgs=[
        ("b", "Forwarding to our CFO."),
        ("me", "Thanks! Happy to walk your CFO through the numbers.")]),

    # ------------------------------------------------------------------ went quiet: buyer non-committal, then silence (near-misses)
    T(Q, "Mar 2025", "Operations Manager", near=True, note="'will get back to you' is not a position", msgs=[
        ("b", "Thanks, will review with the team and get back to you."),
        ("me", "Sounds good. Let me know if questions come up."),
        ("me", "Hi {first}, any update from the team?")]),
    T(Q, "Oct 2025", "HR Director", near=True, note="buyer's last message is scheduling logistics", msgs=[
        ("b", "Can we move our call to next week?"),
        ("me", "Sure, how about Tuesday at 2?")]),
    T(Q, "May 2025", "IT Director", near=True, note="'comparing options' is not a position", msgs=[
        ("b", "We're comparing a few options right now."),
        ("me", "Makes sense. Here's a comparison sheet that might help."),
        ("me", "Happy to jump on a call to go through it.")]),
    T(Q, "Jan 2025", "Customer Care Manager", near=True, note="missed meeting", msgs=[
        ("b", "Can you do a call Friday?"),
        ("me", "Friday 11am works, invite sent."),
        ("me", "Sorry we missed each other Friday! Want to reschedule?")]),
    T(Q, "Dec 2025", "Head of People Operations", near=True, note="'I'll come back to you' is not a position", msgs=[
        ("b", "Thanks, this is useful. I'll come back to you."),
        ("me", "Great, speak soon!"),
        ("me", "Hi {first}, just checking in.")]),

    # ------------------------------------------------------------------ went quiet: seller outreach with no reply at all
    T(Q, "Oct 2025", "Head of Support", msgs=[
        ("me", "Hi {first}, saw you're hiring 10 support agents. Worth a quick chat about onboarding them faster?"),
        ("me", "Bumping this up in case it got buried."),
        ("me", "Last note from me. If this isn't a priority, no worries.")]),
    T(Q, "Jul 2025", "Operations Director", msgs=[
        ("me", "Hi {first}, here's the proposal we discussed on the call."),
        ("me", "Any questions on the proposal?"),
        ("me", "Would it help if I walked your team through it?")]),
    T(Q, "Dec 2025", "Clinic Operations Manager", msgs=[
        ("me", "Hi {first}, quick question: how are you handling shift swaps across your three clinics today?")]),
    T(Q, "Sep 2024", "IT Security Lead", msgs=[
        ("me", "Following up on our call. Here are the answers to your security questions."),
        ("me", "Checking in: did the security team get what they needed?")]),
    T(Q, "Jan 2026", "CFO", msgs=[
        ("me", "Hi {first}, congrats on the Series B! Teams your size usually hit AP bottlenecks around now. Worth a chat?"),
        ("me", "Following up on the above.")]),
    T(Q, "Jul 2026", "Head of Workforce Management", msgs=[
        ("me", "Here's the summary from your two-week trial: 38% fewer manual approvals."),
        ("me", "Would you like to extend the trial or talk pricing?")]),
    T(Q, "Aug 2026", "Director of Customer Operations", msgs=[
        ("me", "Hi {first}, following up on the renewal comparison I sent.")]),
    T(Q, "Jun 2026", "VP IT", msgs=[
        ("me", "Hi {first}, great chatting at the conference! Here's the deck I mentioned."),
        ("me", "Would love to hear what you thought.")]),
    T(Q, "Oct 2024", "Head of Customer Support", msgs=[
        ("me", "Hi {first}, I noticed your team posted three support manager roles. Happy to share how others scaled their help desk without adding headcount.")]),
    T(Q, "Nov 2025", "Director of Operations", msgs=[
        ("me", "Hi {first}, circling back on the pilot results. Do you want to discuss next steps?")]),
    T(Q, "Aug 2025", "Scheduling Manager", msgs=[
        ("me", "Hi {first}, sharing a quick 2-minute video on how we handle overtime rules."),
        ("me", "Did the video make sense?")]),
    T(Q, "Mar 2025", "Finance Director", msgs=[
        ("me", "Hi {first}, congrats on the new role! Would love to show you what we do for finance teams."),
        ("me", "Hi {first}, one more try: worth 15 minutes?")]),
    T(Q, "Jul 2026", "VP Customer Support", msgs=[
        ("me", "Following up on our demo last week. Here's the recording and the pricing we discussed.")]),
    T(Q, "Nov 2024", "Controller", msgs=[
        ("me", "Hi {first}, attached is the ROI calculator with your numbers plugged in."),
        ("me", "Did the ROI numbers look right to you?")]),
    T(Q, "Apr 2025", "Finance Operations Manager", msgs=[
        ("me", "Hi {first}, you downloaded our AP benchmark report. Happy to walk through how you compare.")]),
    T(Q, "Jan 2025", "Head of Finance", msgs=[
        ("me", "Hi {first}, happy new year! Is AP automation on the 2025 plan?")]),
    T(Q, "Jun 2026", "HR Director", msgs=[
        ("me", "Hi {first}, it's been a while! We've launched the Workday integration you asked about.")]),

    # ------------------------------------------------------------------ went quiet: the seller's own words sound like a deferral (near-misses)
    T(Q, "May 2026", "VP Finance", near=True, note="deferral words are the seller's", msgs=[
        ("me", "Hi {first}, totally understand if now isn't the time. Happy to revisit next quarter, just let me know.")]),
    T(Q, "Feb 2025", "Director of Finance", near=True, note="seller offers to hold pricing for budget season", msgs=[
        ("me", "Hi {first}, I know budget season is coming up. I can hold the current pricing until the end of March if that helps.")]),
    T(Q, "Jun 2025", "Head of Support", near=True, note="seller says 'pick this back up'", msgs=[
        ("me", "Hope the product launch went well! Happy to pick this back up whenever things settle on your side.")]),
    T(Q, "Nov 2024", "IT Manager", near=True, note="seller's breakup email says 'timing isn't right'", msgs=[
        ("me", "Hi {first}, worth 15 minutes?"),
        ("me", "Hi {first}, circling back."),
        ("me", "Hi {first}, closing the loop. I'll assume the timing isn't right.")]),
    T(Q, "Sep 2025", "Security Awareness Lead", near=True, note="seller assumes the buyer is busy until January", msgs=[
        ("me", "Since your team is heads-down until the new year, I'll check back in January. In the meantime, here's a short case study.")]),
    T(Q, "Jul 2025", "COO", near=True, note="seller asks which quarter suits", msgs=[
        ("me", "Hi {first}, the proposal is attached. Let me know if Q3 or Q4 works better to kick off.")]),
    T(Q, "Apr 2026", "Director of HR Operations", near=True, note="seller says 'reach out when ready'", msgs=[
        ("me", "No pressure. I know Q2 is busy. I'll leave this with you, and you can reach out when you're ready.")]),
    T(Q, "Sep 2025", "Support Team Lead", near=True, note="a person's 'trial ends tomorrow' email", msgs=[
        ("me", "Hi {first}, your trial ends tomorrow. Want me to extend it?")]),
    T(Q, "May 2025", "Operations Manager", near=True, note="seller suggests September", msgs=[
        ("me", "Just a thought: a lot of teams start after their summer peak. Should I check back in September?")]),

    # ------------------------------------------------------------------ not sales: auto-replies with return dates (near-misses)
    T(N, "Jul 2025", "VP Operations", near=True, note="out-of-office with a return date", msgs=[
        ("b", "I'm out of the office until July 21 with limited access to email. For urgent matters, please contact {first2}.")]),
    T(N, "Nov 2025", "Head of Finance", near=True, note="parental-leave auto-reply", msgs=[
        ("b", "I'm on parental leave until the new year and won't be checking email. I'll respond when I'm back.")]),
    T(N, "Mar 2026", "IT Director", near=True, note="travel auto-reply", msgs=[
        ("b", "Thanks for your email. I'm travelling for our annual conference until March 14 and will get back to you after that.")]),
    T(N, "Apr 2026", "Customer Support Manager", near=True, note="short auto-reply", msgs=[
        ("b", "Out until Monday. Will reply then.")]),
    T(N, "Jan 2026", "Director of Operations", near=True, note="sabbatical auto-reply with a date", msgs=[
        ("b", "I'm on sabbatical until September 2026. Your email will not be forwarded. Please contact {first2} for anything urgent.")]),
    T(N, "Oct 2025", "Procurement Manager", near=True, note="auto-reply naming the vendor evaluation", msgs=[
        ("b", "I'm out until the 12th. For anything related to the vendor evaluation, please contact {first2}, who is covering.")]),
    T(N, "Dec 2025", "unknown", near=True, note="office-closed auto-reply", msgs=[
        ("x:{company} Front Desk", "Our office is closed for the holidays until January 5. We'll respond to your message when we return.")]),
    T(N, "Aug 2025", "unknown", near=True, note="left-the-company auto-reply", msgs=[
        ("x:Mail system", "Please note {first} no longer works at {company}. For finance matters, please contact {email}.")]),

    # ------------------------------------------------------------------ not sales: product notifications that sound like follow-ups (near-misses)
    T(N, "Feb 2026", "unknown", near=True, note="trial-expiry notice", msgs=[
        ("x:Product notifications", "Your free trial ends in 3 days. Upgrade now to keep your dashboards, or pick up where you left off any time.")]),
    T(N, "May 2025", "unknown", near=True, note="trial-ended notice", msgs=[
        ("x:Product notifications", "Your trial has ended. Reactivate within 30 days to restore your workspace.")]),
    T(N, "Jun 2026", "unknown", near=True, note="calendar notice 'moved to next quarter'", msgs=[
        ("x:Calendar", "Invitation updated: Quarterly business review. Moved to next quarter by the organizer.")]),
    T(N, "Sep 2025", "unknown", near=True, note="calendar decline with 'another time'", msgs=[
        ("x:Calendar", "Declined: Follow-up call. Note from organizer: \"Let's find another time.\"")]),
    T(N, "Jan 2025", "unknown", near=True, note="calendar acceptance", msgs=[
        ("x:Calendar", "Accepted: Intro call, {company} and us.")]),
    T(N, "Mar 2025", "unknown", near=True, note="support ticket 'reopen'", msgs=[
        ("x:Support", "Ticket #48213 has been resolved. Reply to this email to reopen it.")]),
    T(N, "Jul 2026", "unknown", near=True, note="newsletter with 'revisit'", msgs=[
        ("x:Newsletter", "Revisit your 2026 goals: our mid-year planning template is here.")]),
    T(N, "Oct 2024", "unknown", near=True, note="podcast about 'not right now'", msgs=[
        ("x:Podcast", "New episode: how top AEs handle 'not right now'. Listen in 20 minutes.")]),

    # ------------------------------------------------------------------ not sales: recruiting, internal and other noise
    T(N, "Nov 2025", "unknown", near=True, note="recruiter outreach", msgs=[
        ("x:Recruiter, TalentBridge", "Hi {me}, I came across your profile and think you'd be a great fit for a Senior Account Executive role at a fast-growing fintech. Open to a chat?")]),
    T(N, "Apr 2025", "unknown", near=True, note="recruiter follow-up", msgs=[
        ("x:Recruiter, Northpeak Search", "Following up on my last note about the Head of Sales role. Would next week work for a quick call?")]),
    T(N, "Aug 2026", "unknown", msgs=[("x:People team", "We're hiring SDRs! Know anyone? The referral bonus is $2,000.")]),
    T(N, "Mar 2026", "unknown", near=True, note="colleague asking to cover a demo", msgs=[
        ("x:{first2} (Account Executive)", "Hey, can you cover my 3pm demo? Something came up.")]),
    T(N, "Feb 2025", "unknown", near=True, note="internal pipeline reminder", msgs=[
        ("x:Sales manager", "Reminder: pipeline review moves to Thursday. Please update your forecast by Wednesday EOD.")]),
    T(N, "Jun 2025", "unknown", msgs=[("x:Billing", "Your invoice INV-20431 for June is attached. Payment is due within 30 days.")]),
    T(N, "Sep 2024", "unknown", msgs=[("x:Newsletter", "This month in support ops: five ways teams cut first-response time. Read the full issue on our blog.")]),
    T(N, "Sep 2025", "unknown", msgs=[("x:Events team", "You're invited: 'Closing the books faster', a live webinar on October 14. Save your seat.")]),
    T(N, "Dec 2024", "unknown", msgs=[("x:IT", "Your password will expire in 7 days. Update it from your account settings.")]),
    T(N, "May 2026", "unknown", msgs=[("x:Network", "{first} viewed your profile. See who else is looking.")]),
    T(N, "Jan 2026", "unknown", msgs=[("x:Customer feedback", "How did we do? Rate your recent support experience in one click.")]),
    T(N, "Apr 2026", "unknown", msgs=[("x:Events team", "Early-bird pricing for RevOps Summit ends Friday. Register now.")]),
    T(N, "Oct 2025", "unknown", msgs=[("x:Partnerships", "Our partner program just launched: refer a customer and earn 20% for a year.")]),
    T(N, "Nov 2024", "unknown", msgs=[("x:IT", "Scheduled maintenance: email may be unavailable Saturday 2 to 4am.")]),
    T(N, "Jul 2025", "unknown", msgs=[("x:People team", "Open enrolment for benefits closes on the 30th.")]),
    T(N, "May 2026", "unknown", near=True, note="post-event marketing", msgs=[
        ("x:Events team", "Thanks for visiting our booth at SaaS Connect! Here are the slides from the keynote.")]),
    T(N, "Feb 2026", "unknown", msgs=[("x:Orders", "Your order has shipped and will arrive Thursday.")]),
    T(N, "Aug 2025", "unknown", msgs=[("x:Mail Delivery Subsystem", "Delivery has failed to these recipients: {email}. The address couldn't be found.")]),
    T(N, "Dec 2025", "unknown", msgs=[("x:Legal", "We've updated our privacy policy. No action is needed.")]),
    T(N, "Jun 2026", "unknown", msgs=[("x:Events team", "Starting in 1 hour: 'Workforce planning for peak season'. Join here.")]),
    T(N, "Aug 2026", "unknown", msgs=[("x:Finance team", "Expense reports for August are due Friday.")]),
    T(N, "Mar 2025", "unknown", msgs=[("x:Community", "Top posts this week in the Support Leaders community.")]),
    T(N, "Jul 2026", "unknown", msgs=[("x:Platform alerts", "Your API usage reached 80% of your monthly limit.")]),
    T(N, "Oct 2025", "unknown", msgs=[("x:Team chat", "You have 12 unread messages in #deals.")]),
    T(N, "Jan 2026", "unknown", msgs=[("x:Careers", "Thank you for applying to the Customer Success Manager role. We'll be in touch.")]),
    T(N, "Apr 2025", "unknown", msgs=[("x:Newsletter", "The Finance Ops Weekly: why AP teams are shrinking (and what they do instead).")]),
]
