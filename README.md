# Provenance Guard

> ### ðŸ‘‹ Start here
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

<!-- â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• UNIT 7 â€” THE BUILD â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->

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
`400 text_too_short`, `400 invalid_creator_id`, `413 text_too_long`, `413 request_too_large` (when
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
`404 not_found` (no decision with that id), `413 request_too_large` (body over
1 MB). Appealing twice is allowed; each
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
     the signal yet â€” and unit 8's attack set is built out of blind spots. -->

### Signal one â€” the model signal

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
And it's English only: GPT-2 was trained on English, and the word counter only
counts a-z and 0-9, so text in another script is refused as too short instead of
being given a label that would mean nothing.

### Signal two â€” the style signal

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

**The rule:** Average the two signals with equal weight. But if they land on
opposite sides of 0.5 and are at least 0.4 apart, hold the result inside the
unsure band (0.35 to 0.70). I wrote this down before coding it. Equal weights
because each signal wrongly suspects a different kind of human writer: the
model signal suspects plain writing and the style signal suspects formal
writing, so neither earned more trust. The cap is there because a plain average
can still turn a split into a verdict: model 1.0 and style 0.45 average to
0.725, which would be an AI label while one method says "human".

**The numbers** (all in `config.py`):

| Setting | Value |
|---|---|
| Model weight / style weight | 0.5 / 0.5 |
| Disagreement gap that triggers the cap | 0.4 |
| Inside the style signal: spread weight / vocabulary weight / punctuation weight | 0.6 / 0.4 / 0 |
| Spread anchors (scores 1.0 at or below / 0.0 at or above) | 0.15 / 0.60 |
| Vocabulary anchors (scores 0.0 at or below / 1.0 at or above) | 0.72 / 0.90 |
| Label thresholds | human below 0.35, AI above 0.70, both boundaries are unsure |
| Model signal curve (given, unchanged) | perplexity 45 maps to 0.5, steepness 1.6 |

**Where it lives:** `scoring.py::combine_signals`

**Calibration run** (`python calibrate.py`, real output). Human texts are
pre-LLM published prose; AI texts came from a chatbot.

```
input                 ppl     model    spread       ttr     punct     style  combined     guess
clearly_ai           12.8     0.882     0.222     0.885     0.101     0.871    0.8765        ai
clearly_ai_2         17.0    0.8265     0.143     0.878     0.079    0.9506    0.8886        ai
clearly_human        50.5    0.4538     0.721     0.711      0.13       0.0    0.2269     human
plain_human          42.2     0.526     0.494     0.798     0.059    0.3148    0.4204    unsure
formal_human         50.4    0.4548     0.273     0.829     0.039    0.6782    0.5665    unsure
edited_ai            22.1    0.7571     0.323       0.9     0.099      0.77    0.7635        ai
```

Where they agree: both signals call the chatbot paragraphs AI (0.83-0.95) and
Twain human (model 0.45, style 0.00). Clearly-AI and clearly-human end up about
0.65 apart.

**A case where my two signals split, and what my rule does with it:** Orwell's
1946 essay. The model signal reads it as human (0.45, perplexity 50, lots of
rare words), but the style signal reads it as AI (0.68), because Orwell writes
long sentences of similar length with varied vocabulary, which is exactly the
chatbot shape. The gap is 0.22, under the 0.4 cap, so the rule just averages:
0.57, unsure. That's the right outcome, and it's also the closest call in the
set. It's 0.13 below the AI line, and that headroom is why the AI threshold is
0.70 and not the starter's 0.65. Hemingway splits the other way (model 0.53,
style 0.31) and lands at 0.42, also unsure.


---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 up to (not including) 0.35 | This looks like it was written by a person. Our automated check didn't find the patterns we usually see in AI-generated writing. |
| unsure | 0.35 to 0.70, both ends included | We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide. |
| high-confidence AI | above 0.70 up to 1.00 | This reads a lot like AI-generated writing. Automated checks like ours can be wrong, so if you wrote this yourself, you can ask for a person to review it. |

The text lives in `scoring.py` (`LABEL_HUMAN`, `LABEL_UNSURE`, `LABEL_AI`) and
the mapping in `scoring.py::score_to_label`. There's no gap: every score from
0 to 1 maps to exactly one label, which a unit test checks in steps of 0.01.
All three are reachable with real text; see the calibration table above (Twain
got human, Hemingway got unsure, the chatbot paragraphs got AI) and the Sample
Run below.

**Why I worded the "unsure" one this way:** The person reading it probably
wrote every word, so it can't sound like a softer accusation. It says plainly
that the check couldn't decide, tells them they're in good company ("a lot of
people's own writing ends up here"), and says out loud that it's not a
judgment about them. I kept numbers and words like "confidence" out of all
three, because a score of 0.42 means nothing to a writer. The AI label is the
only one that mentions review, because it's the only one where someone has a
reason to want it.



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
  -d '{"text": "Artificial intelligence has become an increasingly important part of modern society. It offers numerous benefits across a wide range of industries, including healthcare, education, and finance. By automating routine tasks, AI allows professionals to focus on more meaningful work. However, it is important to consider the ethical implications of these technologies. Ensuring fairness, transparency, and accountability is essential for building trust. Ultimately, the responsible development of AI will play a key role in shaping a better future for everyone.", "creator_id": "writer_ana"}'
```

```json
{"confidence":0.8765,"content_id":"b7bd3598-3e72-4cf3-bacc-8765acafaef7","creator_id":"writer_ana","guess":"ai","label":"This reads a lot like AI-generated writing. Automated checks like ours can be wrong, so if you wrote this yourself, you can ask for a person to review it.","model_score":0.882,"status":"decided","style_score":0.871}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "b7bd3598-3e72-4cf3-bacc-8765acafaef7", "reasoning": "I wrote this for my intro to tech ethics class. I write in a pretty textbook way because that is how we were taught to write summaries."}'
```

```json
{"content_id":"b7bd3598-3e72-4cf3-bacc-8765acafaef7","message":"Thanks. Your appeal has been recorded and a person will review this decision. Until then it's marked as under review.","status":"under_review"}
```

**What the log shows afterwards** (the original decision line, then the appeal
right after it; nothing was overwritten)

```bash
$ curl "http://127.0.0.1:5000/log"
```

```json
{"timestamp": "2026-11-01T01:31:09+00:00", "content_id": "b7bd3598-3e72-4cf3-bacc-8765acafaef7", "creator_id": "writer_ana", "guess": "ai", "model_score": 0.882, "style_score": 0.871, "combined_score": 0.8765, "label": "This reads a lot like AI-generated writing. Automated checks like ours can be wrong, so if you wrote this yourself, you can ask for a person to review it.", "status": "decided", "word_count": 79}
{"content_id": "b7bd3598-3e72-4cf3-bacc-8765acafaef7", "creator_id": "writer_ana", "event": "appeal", "reasoning": "I wrote this for my intro to tech ethics class. I write in a pretty textbook way because that is how we were taught to write summaries.", "status": "under_review", "timestamp": "2026-11-01T01:31:19+00:00"}
```

**The item's status afterwards** (stretch: `GET /content/<id>`)

```bash
$ curl http://127.0.0.1:5000/content/b7bd3598-3e72-4cf3-bacc-8765acafaef7
```

```json
{"appeal_count":1,"confidence":0.8765,"content_id":"b7bd3598-3e72-4cf3-bacc-8765acafaef7","creator_id":"writer_ana","guess":"ai","label":"This reads a lot like AI-generated writing. Automated checks like ours can be wrong, so if you wrote this yourself, you can ask for a person to review it.","model_score":0.882,"status":"under_review","style_score":0.871,"submitted_at":"2026-11-01T01:31:09+00:00"}
```

**Bad input, and what it leaves in the log**

```bash
$ curl -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" \
  -d '{"text": "", "creator_id": "writer_ana"}'
{"error":"invalid_text","message":"\"text\" must be a non-empty string."}      # HTTP 400

$ curl -X POST http://127.0.0.1:5000/appeal -H "Content-Type: application/json" \
  -d '{"content_id": "not-a-real-id", "reasoning": "mine"}'
{"error":"not_found","message":"We couldn't find a submission with that id."}  # HTTP 404

$ curl "http://127.0.0.1:5000/log?limit=2"
{"count":2,"entries":[{"creator_id":"writer_ana","event":"rejected","reason":"invalid_text","route":"submit","status":"rejected","timestamp":"2026-11-01T01:31:19+00:00"},{"creator_id":"unknown","event":"rejected","reason":"not_found","requested_content_id":"not-a-real-id","route":"appeal","status":"rejected","timestamp":"2026-11-01T01:31:19+00:00"}]}
```

The other two labels, from the same run: Twain's opening scored 0.2269
(human) and Hemingway's scored 0.4204 (unsure). The first entry in
`logs/audit.jsonl` is from Milestone 3, before the style signal and labels
existed, which is why it has `style_score` 0.5 and a placeholder label. I left
it there because the log is append-only.

**Tests:** `python -m unittest discover tests` runs 59 unit tests (route
contract, every bad-input case, the appeal path, the combining rule, label
coverage, each style measure). The detector is stubbed in route tests so they
run in under a second.

---

## How I Used AI

**Moment 1**

- *What I asked for:* I had an AI assistant implement the three style measures
  following the hints in `stylometry.py`, then run both signals over six
  calibration texts (`calibrate.py`) before deciding any weights.
- *What came back:* The raw table. Two things in it didn't match the hints. AI
  text had *higher* vocabulary variety than the human texts (0.88 vs
  0.71-0.83), not lower, and punctuation density didn't separate AI from human
  at all.
- *What I changed:* I went with the data, not the hint. Vocabulary variety
  now counts as AI-like when it's high, punctuation gets weight 0 (still
  printed so I can see it in unit 8), and the spread and vocabulary anchors in
  `config.py` are rounded from that table. I also moved the AI threshold from
  0.65 to 0.70 after seeing Orwell land at 0.57.

**Moment 2**

- *What I asked for:* A second AI session with a fresh context reviewed the
  finished routes. I asked it to find any input that makes `/submit` or
  `/appeal` return a 500 instead of a 4xx, and to prove each one by running it.
- *What came back:* Five findings. Two were real 500s: a lone UTF-16 surrogate
  like `"\ud800"` parses as JSON but crashes the log write, and deeply nested
  JSON (`[[[[...`) raises a `RecursionError` that `get_json(silent=True)`
  doesn't catch. It also found that a `creator_id` made of a zero-width space
  counted as "not blank", that `"' ' '"` counted as words, and that a 413 on
  `/appeal` was logged as `text_too_long`.
- *What I changed:* I wrote a failing test for each one first, then fixed them
  in `app.py` (`_json_body`, `_clean_str`, a renamed `request_too_large` code)
  and in `stylometry.py::words`. I didn't take one suggestion: it pointed out
  the label is computed from the rounded score, but that's on purpose, so
  the label always agrees with the number the writer sees. Its point that
  non-English text gets refused I kept as a known limitation, not a fix, since
  GPT-2 here is an English model.

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• UNIT 8 â€” THE TEST â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently â€” one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run â€” Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** â€” the one I'd least want to explain to a writer
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
                        word variety, and typos raise word variety â€” so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run â€” After

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



<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

     SUBMISSION CHECKLIST â€” unit 7

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
       [ ] Repository URL submitted â€” WRITE IT DOWN

     SUBMISSION CHECKLIST â€” unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack â€” stage AND mechanism
       [ ] One improvement, with Attack Run â€” After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->

---

ðŸ“– **How to run this project: [RUNNING.md](RUNNING.md)**
