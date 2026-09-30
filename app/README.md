# Reopen Inbox — the mock app

A local web app for running the newsletter's test. You load a set of dead email threads plus your answer key.
Then you run Jev and an LLM over every thread and read off the numbers for §05–§06.

```bash
cd sales-pipeline-revival-jev
.venv/bin/python app/server.py                         # the 300-thread sample set in data/
.venv/bin/python app/server.py --data datasets/mine    # your own set
```

Then open **http://127.0.0.1:8765**. The server only listens on your own machine. Stop it with Ctrl+C.

## Keys (in `.env`, never committed)

```
TYPESAFE_API_KEY=...
GEMINI_API_KEY=...         # the LLM baseline (Gemini 3.8 Flash)
```

Restart the app after changing `.env`. Keys are sent only to TypeSafe or Google, never to the page.

## Your dataset

A folder with two files. Use synthetic or anonymized threads, since it goes on GitHub.

**`threads.jsonl`**: one thread per line.

```json
{"id": "m001", "contact_role": "VP Operations", "last_message_sent": "March 2026",
 "messages": [{"from": "seller (me)", "text": "Here's the proposal we discussed."},
              {"from": "Dana Reyes (VP Operations, Acme)", "text": "Looks good, but let's revisit after our Q3 budget review."}]}
```

- `last_message_sent` is a full month name plus the year.
- Put `seller` or `(me)` in `from` for your own messages. The page draws them differently, and it shows the model who spoke last.

**`labels.csv`**: the answer key. Write it **before** you run any model.

```
id,label,timeframe,near_miss,reopen_worthy
m001,soft_deferral,3_to_6_months,False,True
```

| Column | Allowed values |
|---|---|
| `label` | `soft_deferral`, `hard_no`, `went_quiet`, `not_sales` |
| `timeframe` | `within_3_months`, `3_to_6_months`, `6_to_12_months`, `over_a_year`, `not_stated` |
| `near_miss` | `True` for tricky threads (a polite hard no, a brush-off "maybe later", out-of-office replies, recruiter emails) |
| `reopen_worthy` | `True` if you'd actually reopen it now |

`--as-of 2026-10` sets the month your test treats as "today". It is used to judge whether the awaited moment has arrived.

The app lists any problems in your files at the top of the page. Fix them and reload.

## Running the test

1. **Inbox:** spot-check a few threads with **Run** before spending on the whole set.
2. **Run Jev on all**, then **Run LLM on all**. Eight calls go out in parallel. Answers are cached in `runs/`, so a re-run only calls threads that are new or edited.
3. **Reopen list:** the top 10 by warmth, checked against your key. This is precision@10.
4. **Results:** both models side by side, a calibration chart, the confusion table and every miss.
   **Numbers for the newsletter** gives one line per orange placeholder on the page, ready to copy.
5. **Try a thread:** paste any thread and get a live Jev answer. It is not added to the results.

**Correcting the answer key.** Open a thread and click **Correct** under it. Corrections are saved to
`answer_key_edits.json` in the dataset folder, and `labels.csv` is left untouched. Each correction records the original
answer, and whether a model had already answered that thread. Corrections made after a run are flagged on the Results
tab so you can disclose them. **Undo correction** restores the original.

**Results file.** Every time the Results tab loads, the numbers are also saved as `results.json` in the dataset folder
(or use **Download results.json**).

Don't edit the questions in `jevlib.py` after you've seen results. If you want to tune them, tune on a separate small set.

## For the GitHub repo

Commit `runs/`: readers can then reproduce every number without an API key.
Never commit `.env`; it is already in `.gitignore`.
