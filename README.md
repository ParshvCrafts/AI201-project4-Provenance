# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard is a small Flask service that takes a piece of writing, guesses
whether it was written by a person or by AI, and shows a plain-English label.
If the writer thinks it got them wrong, they can appeal.

**The path one submission takes:**

1. **The route (`app.py::submit`)** receives `POST /submit` with `text` and
   `creator_id`. It checks the input first: missing, empty or non-string text,
   fewer than 20 words, more than 20,000 characters, or no `creator_id` all get
   a 4xx with a JSON error, and the rejection is still written to the log.
   Adds: a guarantee that everything after this step has real text to work on.
2. **The route gives it an id.** A fresh `content_id` (UUID4). Adds: a handle
   the writer needs later to appeal or look the item up.
3. **Signal one (`detector.py::model_signal`)** runs GPT-2 locally and measures
   how predictable the text is (perplexity), squashed to 0-1. Adds: a
   "does this read like a model wrote it" score, `model_score`.
4. **Signal two (`stylometry.py::style_signal`)** measures the shape of the
   text without reading it: how much sentence lengths vary and how varied the
   vocabulary is. Adds: `style_score`, also 0-1, higher means more AI-like.
5. **The combining rule (`scoring.py::combine_signals`)** averages the two and
   holds the result in the unsure band when the signals strongly disagree.
   Adds: one number, `confidence` (0 = human, 1 = AI).
6. **The label mapping (`scoring.py::score_to_label`)** turns that number into
   one of three sentences written for a person, plus a short `guess`
   (`human` / `unsure` / `ai`). Adds: something a reader can understand.
7. **The audit log (`audit.py::log_decision`)** writes one JSON line to
   `logs/audit.jsonl` with all three scores, the guess, the label and status
   `decided`. Then the route returns the response. Adds: a record that can be
   read back, appealed against and diagnosed later.

### Tracing the false positive

Say a student who learned English as a second language writes a 200-word
reflection in short, plain sentences with common words. They wrote every word.

- **Signal one** finds the text very predictable, because common words in
  ordinary order are exactly what GPT-2 expects. It might give 0.85.
- **Signal two** depends on their habits. If their sentences vary in length it
  gives something like 0.3, and the two signals now disagree by more than 0.4
  on opposite sides of 0.5. The combining rule holds the score in the unsure
  band, so they see the unsure label, not an accusation.
- The bad case is when their sentences are also even in length. Then style
  might give 0.7, the average is 0.775, and they get the high-confidence AI
  label. That is the person my thresholds are set for: the AI label needs a
  score above 0.70, not 0.65, and I'd rather let some AI text through as
  "unsure" than put this label on them.
- **What the label says to them:** that it looks a lot like AI writing, that
  checks like this can be wrong, and that they can appeal.
- **What they can do:** `POST /appeal` with their `content_id` and why they
  think it's wrong. The item moves to `under_review`, the appeal is logged
  right after the original decision (nothing is overwritten), and they get a
  confirmation. A person reviews it; nothing re-scores it automatically.

### The endpoint contracts

All requests and responses are JSON. Every error response has the same shape:
`{"error": "<code>", "message": "<sentence a person can read>"}`.

**`POST /submit`**

| Request field | Type | Rules |
|---|---|---|
| `text` | string | required, at least 20 words, at most 20,000 characters |
| `creator_id` | string | required, not blank, at most 100 characters |

| Response field (200) | Type | Meaning |
|---|---|---|
| `content_id` | string | UUID4, used by `/appeal` and `/content/<id>` |
| `creator_id` | string | echoed back, trimmed |
| `guess` | string | `"human"`, `"unsure"` or `"ai"` |
| `confidence` | float | combined score, 0.0 (human) to 1.0 (AI), 4 decimals |
| `label` | string | the full sentence a reader sees |
| `model_score` | float | signal one, 0-1, higher = more AI-like |
| `style_score` | float | signal two, 0-1, higher = more AI-like |
| `status` | string | always `"decided"` on a new submission |

Errors: `400 invalid_json` (body isn't a JSON object), `400 invalid_text`,
`400 text_too_short`, `400 invalid_creator_id`, `413 text_too_long` (also when
the raw body is over 1 MB), `503 detector_unavailable` (the model couldn't load).

**`POST /appeal`**

| Request field | Type | Rules |
|---|---|---|
| `content_id` | string | required, must be an id `/submit` returned |
| `reasoning` | string | required, not blank, at most 5,000 characters |

| Response field (200) | Type | Meaning |
|---|---|---|
| `content_id` | string | echoed back |
| `status` | string | always `"under_review"` |
| `message` | string | confirmation for the writer |

Errors: `400 invalid_json`, `400 invalid_content_id`, `400 invalid_reasoning`,
`404 not_found` (no decision with that id). Appealing twice is allowed; each
appeal is logged and the status stays `under_review`.

**`GET /content/<content_id>`** (stretch, see below) returns the original
decision fields plus the current `status` and `appeal_count`, or `404 not_found`.

### Stretch features I'm adding

Only **`GET /content/<id>`**, which returns one item's current status. I'm
skipping the third signal (punctuation didn't separate AI from human in my
calibration, so a "third signal" would get a weight near zero) and the
verified-human path (it needs credential storage and a whole extra flow).


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to GPT-2, running locally
(`detector.py::model_signal`). It computes perplexity over the first 400 tokens
and maps it to 0-1 with a logistic curve centred at perplexity 45. Low
perplexity means a high score, which means more AI-like.

**Why that might differ between human and AI writing:** A language model writes
by picking likely next words, so its output is text a language model finds easy
to predict. People take odd turns and pick specific words. In my calibration,
chatbot paragraphs had perplexity 13-22 (scores 0.76-0.88) and pre-LLM human
paragraphs had 42-51 (scores 0.45-0.53).

**What it can't see:** Who wrote it. It measures predictability, and plain
writing is predictable whoever wrote it: second-language writers, younger
writers, anyone keeping it simple. It also can't see an AI text that was
prompted to use rare words or was paraphrased into stranger phrasing, and it
only reads the first 400 tokens, so anything after that is invisible to it.

### Signal two — the style signal

**What it measures:** The shape of the text, without reading it
(`stylometry.py::style_signal`). Two measures count toward the score:
sentence length spread (stdev / mean of words per sentence) and vocabulary
variety (moving-average type-token ratio over 50-word windows, so length
doesn't skew it). A third, punctuation density, is computed and shown but
weighted 0, because it didn't separate AI from human in my calibration.

**Why that might differ between human and AI writing:** Chatbot prose marches
in step: my AI samples had spread 0.14-0.22 while human samples ran 0.27-0.72.
Vocabulary went the opposite way from what I expected: the chatbot paragraphs
had *higher* variety (0.88) than the human ones (0.71-0.83), because the model
avoids repeating words while people happily repeat "truth" and "book" and a
name. So high variety points toward AI in my scoring.

**What it can't see:** Meaning. Anything that changes the shape without
changing the substance moves it: splitting or merging sentences, adding typos
(which raise vocabulary variety), pasting in a quotation. It is cheap to fool on
purpose. It also needs at least two sentences to say anything about spread, and
formal human writing with even sentence lengths (Orwell scored 0.68) looks
AI-like to it.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:**

**The numbers:**

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "creator_id": "..."}'
```

```json

```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
