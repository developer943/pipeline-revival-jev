# Dated, not dead: Jev vs Gemini on 203 dead sales deals

Most "lost" deals were never lost. The buyer said "not right now", and nobody went back.
This repo tests whether a cheap decision model can find those deals in an inbox. It pits
[Jev](https://typesafe.ai/) (TypeSafe's System One model) against Google's Gemini 3.8 Flash
on 203 hand-written email threads. Everything is here, so you can re-run it.

It is the open-source companion to *Dated, Not Dead*, Field Notes Issue 01, from
[Salesgear](https://salesgear.io).

## Results (30 Sep 2026, `jev-1.13.0` vs `gemini-3.8-flash`)

| | Jev | Gemini 3.8 Flash |
|---|---|---|
| Correct category | 95.1% (193 of 203) | **98.0%** (199 of 203) |
| Tricky threads (68) | 88.2% | **94.1%** |
| Real "later" deals found | 60 of 61 | 60 of 61 |
| Top 10 worth reopening | 9 of 10 | 9 of 10 |
| Come-back timing right | **92%** | 77% |
| Calibration error (0 is perfect) | **0.020** | 0.023 |
| Cost per 10,000 threads | **$0.45** | $12.34 |
| Time per thread (median) | **0.35 s** | 2.2 s |

**The verdict:** Gemini is a bit more accurate. Jev finds the same deals for about 1/28th of the cost and about
6× faster, which makes it the one you can afford to run on every thread you have. Send anything under 75%
confidence to a person; for Jev that's 7% of threads, holding 6 of its 10 mistakes.

The misses teach the most: both models read a travel out-of-office reply as a deferral and put it in
their top 10. Filter auto-replies and calendar mail in code before the model sees them.

## Run it yourself

Python 3, nothing to install.

```bash
git clone https://github.com/developer943/sales-pipeline-revival-jev
cd sales-pipeline-revival-jev
python3 app/server.py --data datasets/salesgear-v1 --as-of 2026-09
# open http://127.0.0.1:8765 → the Results tab
```

Every model answer is committed under `runs/`, so the Results tab reproduces the table above **with no API key**.
To re-run the models, or to run them on your own threads, create a `.env` file:

```
TYPESAFE_API_KEY=...
GEMINI_API_KEY=...
```

See [app/README.md](app/README.md) for the app and the dataset format.

## What's inside

```
app/                     Reopen Inbox: a local web app that runs both models, ranks the reopen list,
                         scores everything against the answer key, and logs answer-key corrections
datasets/salesgear-v1/   the test set: 203 hand-written threads, answer key, labeling rules
  source.py              every thread and its answer, written before any model saw them
  build.py               → threads.jsonl + labels.csv (reproducible byte for byte)
  LABELING.md            how every answer was decided
  results.json           the scored results behind the table above
jevlib.py                the six typed questions sent to Jev, the API call, the warmth formula
baseline/prompt.py       the baseline's prompt and output schema
baseline/run_gemini.py   the Gemini baseline (standard library only)
eval/metrics.py          accuracy, precision/recall, precision@k, calibration (ECE), cost, time
runs/                    every cached model answer
data/                    an earlier 300-thread practice set (template-generated), with its runs
```

## How the test works

- **The questions.** Each thread goes to Jev in one request with six typed questions:
  - a CHOICE for the category (soft_deferral, hard_no, went_quiet, not_sales) and one for the come-back window;
  - a NOUL for whether the buyer named a trigger;
  - SCOREs for trigger clarity and seniority.
- **Warmth.** Warmth (0–100) is computed in code from those answers. The code also does all date maths,
  because date arithmetic is a documented weak spot for Jev 1.13.
- **The same task for both.** Gemini gets the identical threads, question definitions and answer key, in JSON mode
  with low thinking. The same warmth code scores both, so ranking differences come from the models' judgments alone.
- **Cost.** Costs are real token counts at each provider's list price.

## Limits

- **Synthetic threads.** They were drafted with an AI model from a different family than Gemini, which is why Gemini is the
  baseline. Real inboxes are longer and messier.
- **One run.** One run per model, on one version each; there are no repeat runs to measure variance.
- **One-team labels.** The answer key follows written rules (LABELING.md) and was set by one team.

## About

Built by [Salesgear](https://salesgear.io). Questions or results from your own inbox: open an issue.

## License

MIT. See [LICENSE](LICENSE).
