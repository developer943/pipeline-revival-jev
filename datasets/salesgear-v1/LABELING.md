# salesgear-v1: how the answer key was decided

203 synthetic email threads for the Dated, Not Dead test. Every thread was written by hand for this set, and its label was
fixed at the moment it was written, before any model saw it. No thread comes from a real inbox; all names and companies are
invented. The seller sells one of four fictional products: AP automation, shift scheduling, security awareness or a support
platform.

| Label | Threads | Near-misses |
|---|---|---|
| `soft_deferral` | 61 | 16 |
| `hard_no` | 50 | 17 |
| `went_quiet` | 50 | 14 |
| `not_sales` | 42 | 21 |
| **Total** | **203** | **68 (33%)** |

44 threads are worth reopening. "Today" for this test is **September 2026**, so run the app with `--as-of 2026-09`.

## The four labels

The label is the buyer's **last position** in the thread.

- **`soft_deferral`**: the buyer postponed and invited you back, with or without a time ("reach out in April", "after the
  audit", "down the line").
- **`hard_no`**: the buyer declined, however politely. That includes "we'll reach out if anything changes", where the buyer
  gives no invitation back.
- **`went_quiet`**: the buyer never gave a position. The thread ends on your unanswered message. A buyer message that only
  asks a question, moves a meeting or says "I'll get back to you" is not a position.
- **`not_sales`**: not a sales conversation. This covers auto-replies (including out-of-office replies with a return date),
  notifications, newsletters, invites, recruiters and internal email.

## Rules for the tricky cases

- **The seller spoke last after a deferral.** If the buyer deferred and your acknowledgement ("Talk in April!") is the last
  message, it's still `soft_deferral`. The buyer gave a position.
- **The seller's own words sound like a deferral.** "Happy to revisit next quarter" in *your* message doesn't make it a
  deferral. It's `went_quiet` if the buyer never replied.
- **Brush-offs.** "Sure, try again in 6 months. Can't promise anything" still invites you back, so it's `soft_deferral`.
  It is flagged `brushoff` and never counted as worth reopening.
- **Refusals that mention time.** "No need to circle back next quarter" and "no budget this year or next" are `hard_no`.

## The other columns

| Column | Meaning |
|---|---|
| `timeframe` | Deferrals only: how far after the last message the buyer asked you to come back. Up to 3 months is `within_3_months`, 4–6 is `3_to_6_months`, 7–12 is `6_to_12_months`, more is `over_a_year`, and no timing is `not_stated`. |
| `due` | The month the buyer asked for. `timeframe` is worked out from it. |
| `reopen_worthy` | A genuine deferral (not a brush-off) whose `due` month has arrived by September 2026. Untimed genuine deferrals count after six months. Everything else is `False`. |
| `near_miss` | The thread contains wording typical of a different label, as described in `note`. |
| `months_elapsed` | Months from the last message to September 2026. |

`build.py` works out `timeframe`, `reopen_worthy` and `months_elapsed` from these rules, so they contain no hand-arithmetic.

## Before you publish

- **Review the key yourself.** Open the set in the app (`--data datasets/salesgear-v1`) and filter by label. Change any
  label you disagree with in `source.py`, then run `python3 datasets/salesgear-v1/build.py`.
- **Say who wrote it.** The threads were drafted with an AI model. A baseline from that same model family could find
  the text easier to read, so the baseline is Gemini, from a different family. Say this in the write-up. Better still, replace or add 20–30 threads written
  by you or a colleague.
- **Freeze the set before the first run.** After the first model run, don't edit threads or labels to fix what a model got
  wrong.
