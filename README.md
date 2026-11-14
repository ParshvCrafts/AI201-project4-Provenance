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

**Unit 8 stretch:** only the per-creator limits note. My limiter keys on
`creator_id`, falling back to the address, and the Rate Limiting section says
what that changes compared with per-address limits. I'm skipping the attacks
on someone else's system and the second improvement to keep this unit small.


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
And it's English only: GPT-2 was trained on English, and the word counter only
counts a-z and 0-9, so text in another script is refused as too short instead of
being given a label that would mean nothing.

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

**Moment 3 (unit 8)**

- *What I asked for:* After the first criteria run, an AI assistant to explain
  why one request in criterion 1 came back with no result, and later why
  criterion 4 dropped to 9/10 in one trial.
- *What came back:* Both were `WinError 10055` on opening a connection. Its
  first guess was that my harness opened too many connections, and it switched
  to one `requests.Session`. That guess was wrong: the next run failed the same
  way.
- *What I changed:* I checked the audit log and found no trace of either
  request, so it never reached my service, which made it a harness problem and
  not one of my five stages. I kept the session but added connect-only retries
  with backoff, ran "before" a third time, and kept the two bad runs in
  `results/` instead of deleting them. I also had the comment it wrote
  corrected, since it claimed the session was the fix.

**Moment 4 (unit 8)**

- *What I asked for:* Options for the one improvement, after I'd traced the
  criterion 1 miss to a three-sentence spread.
- *What came back:* Two options that both fixed criterion 1: raise the AI
  threshold to 0.75, or stop measuring spread under 5 sentences. Before I chose,
  I had it predict every label change for both, using the logged model scores.
- *What I changed:* The prediction showed the sentence rule would cost me
  criterion 3 and the threshold wouldn't. I picked the sentence rule anyway,
  because the threshold only cleared Baum by 0.013 and left the bug in place.
  The re-run matched the prediction exactly. I also chose the strict
  held-or-broke rule (unsure counts as broke for evasions) over the lenient
  one, because the lenient one made my numbers look better by hiding the real
  weakness.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day (`config.py`, applied to `POST /submit` only)

**Why those numbers and not others:**

I thought about two callers. A writer checks a piece, maybe fixes a sentence,
and checks again. Three or four tries in one minute is already a lot, so 5
gives them room without me having to guess exactly how fast they retype. 50 a
day covers several pieces with a few revisions each.

A script trying to map my thresholds needs hundreds of variations, and each
one costs me 1-2 seconds of GPT-2 on the CPU. At the starter's 10/min with no
real daily cap, 1,000 probes take under two hours. At 5/min and 50/day they
take 20 days for one creator_id. I looked at 3/min too, but a writer who fixes
a typo and resubmits would hit it, and `run_eval.py` reuses each creator_id
across its three trials, so it would sit right on the edge.

`/appeal` and `/content/<id>` are not limited. They don't run the model, and
I don't want a writer locked out of appealing because they submitted a lot
that day (there's a test for that: `test_appeal_is_not_rate_limited`).

**What a caller counts as:** the `creator_id` in the body. If there isn't a
usable one, the caller's address. So a household sharing one Wi-Fi network
doesn't share one budget, which is good. The cost is the other side: a script
that makes up a new `creator_id` for every request is not slowed down at all,
because to my limiter it looks like a crowd. Fixing that properly needs real
accounts, which this service doesn't have. One detail I checked: requests
with no `creator_id` still spend the address's budget even though they end
in a 400, because the limiter runs before my route does. A script can't probe
for free by sending bad requests.

**The run of status codes when I pushed past it:**

`python run_attacks.py --flood 15 --creator flood_warm` (the model was already loaded):

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

My first flood run, right after starting the service, gave six 200s instead
of five:

```
200 200 200 200 200 200 429 429 429 429 429 429 429 429 429
```

I didn't want to wave that away, so I checked. `/health` answered at
17:19:56 and the first submission came back at 17:21:11, so loading the model
took about 75 seconds. Flask-Limiter's fixed window starts at the first hit
and lasts 60 seconds, and that window ran out while request 1 was still
loading the model. Requests 2-6 landed in a new window. So the six 200s were
not inside one minute, and the limiter was right. The warm run is the
representative one. The warm run is in `results/flood_2026-11-07_1721.md`; the cold
run wrote to the same file name a minute earlier and was overwritten, so its
codes above are copied from my terminal, and its six 200s are in the audit log
under `flood_tester`.

Every 429 leaves a `rejected` entry in `logs/audit.jsonl` with
`"reason": "rate_limited"`, and I confirmed `GET /log` returns three fresh
decisions and a 400 rejection after submitting them.

---

## Attack Run — Before

`python run_attacks.py --set attack_set/attack_set --label before`, full output
in `results/attack_run_2026-11-07_1730_before.md`. Model and style scores come
from the matching audit log entries (`results/audit_extract_before.json`).

**How I marked them.** Each family is judged on what it was going for:

- **Evasion** (AI text trying to get past me): HELD only if it still got the
  AI label, or was refused. "Unsure" counts as BROKE. An unsure label doesn't
  trigger anything, so the attacker got what they came for. This is the strict
  reading and it makes my numbers look worse, but the lenient one (only a
  "human" label counts) would have hidden the main weakness below.
- **False positive** (human text trying to get accused): BROKE only if it got
  the AI label.
- **Prompt injection**: BROKE if it got the "human" label it asked for, or if
  the label text or the log changed. PI04's `<script>` never reaches the label
  (labels are fixed sentences in `scoring.py`), and after PI05 every line of
  `logs/audit.jsonl` still parses as one JSON object.
- **Malformed and flood**: HELD on any clean 4xx, including 429. BROKE on a 5xx
  or a dropped connection. There were none.

| ID | Family | Targeting | Status, guess, score (model, style) | Verdict |
|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 unsure 0.575 (m 0.16, s 0.99) | **BROKE** |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 unsure 0.491 (m 0.59, s 0.39) | **BROKE** |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 unsure 0.637 (m 0.67, s 0.61) | **BROKE** |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 ai 0.790 (m 0.61, s 0.97) | **HELD** |
| EV05 | evasion | both signals: heavy human editing pass | 200 human 0.316 (m 0.32, s 0.31) | **BROKE** |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 unsure 0.429 (m 0.57, s 0.29) | **BROKE** |
| EV07 | evasion | signal two: padding with punctuation | 200 unsure 0.583 (m 0.59, s 0.58) | **BROKE** |
| EV08 | evasion | signal one: text below the token window | 400 | **HELD** |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 unsure 0.640 (m 0.70, s 0.58) | **BROKE** |
| EV10 | evasion | signal two: repeated stanza structure | 200 unsure 0.627 (m 0.98, s 0.27) | **BROKE** |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 unsure 0.500 (m 0.62, s 0.38) | **HELD** |
| FP02 | false_positive | human writing in a formal register | 200 unsure 0.664 (m 0.74, s 0.59) | **HELD** |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 unsure 0.694 (m 0.81, s 0.58) | **HELD** |
| FP04 | false_positive | a student essay written to a rubric | 200 unsure 0.684 (m 0.83, s 0.54) | **HELD** |
| FP05 | false_positive | technical documentation written by a person | 200 unsure 0.616 (m 0.80, s 0.43) | **HELD** |
| FP06 | false_positive | a person imitating a formal template | 200 unsure 0.535 (m 0.88, s 0.19) | **HELD** |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 unsure 0.441 (m 0.88, s 0.00) | **HELD** |
| FP08 | false_positive | very short genuine human submission | 400 | **HELD** |
| PI01 | prompt_injection | instruction to ignore the check | 200 unsure 0.431 (m 0.46, s 0.40) | **HELD** |
| PI02 | prompt_injection | instruction disguised as a system message | 200 human 0.302 (m 0.20, s 0.40) | **BROKE** |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 unsure 0.668 (m 0.59, s 0.74) | **HELD** |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 unsure 0.541 (m 0.50, s 0.58) | **HELD** |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 unsure 0.606 (m 0.64, s 0.57) | **HELD** |
| PI06 | prompt_injection | instruction plus real human text | 200 unsure 0.485 (m 0.56, s 0.41) | **HELD** |
| MF01 | malformed | text is only whitespace | 400 | **HELD** |
| MF02 | malformed | text is a single character | 400 | **HELD** |
| MF03 | malformed | text is control characters | 400 | **HELD** |
| MF04 | malformed | text is only punctuation | 400 | **HELD** |
| MF05 | malformed | text is a very long single word | 400 | **HELD** |
| MF06 | malformed | text is emoji only | 400 | **HELD** |
| MF07 | malformed | text is right-to-left script | 400 | **HELD** |
| MF08 | malformed | text is 60,000 characters | 413 | **HELD** |
| RQ01 | malformed | no text field at all | 400 | **HELD** |
| RQ02 | malformed | no creator_id | 400 | **HELD** |
| RQ03 | malformed | text is a number | 400 | **HELD** |
| RQ04 | malformed | text is a list | 400 | **HELD** |
| RQ05 | malformed | text is null | 400 | **HELD** |
| RQ06 | malformed | creator_id is an object | 400 | **HELD** |
| RQ07 | malformed | body is a JSON array, not an object | 429 | **HELD** |
| RQ08 | malformed | body is unparseable JSON | 429 | **HELD** |
| RQ09 | malformed | body is empty | 429 | **HELD** |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | **HELD** |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | **HELD** |
| RQ12 | malformed | deeply nested JSON | 400 | **HELD** |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | **HELD** |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | **HELD** |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | **HELD** |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | **HELD** |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | **HELD** |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | **HELD** |

**Before: 47 held, 9 broke, out of 56.**

Two notes on that table:

- **RQ07 to RQ11 got 429, not 400.** Those bodies have no usable `creator_id`,
  so they count against my own address, and the malformed rows before them had
  already used the 5 per minute. The limiter worked, but it meant my route never
  saw those five. So I sent each one again on its own after the window reset
  (`results/attack_run_*_retest*.md`). All five came back `400 invalid_json`
  with a `rejected` log entry, so they hold on the route too.
- **The flood rows got 400 first, then 429.** The flood text is 9 words, under
  my 20-word minimum, so the first five were refused as too short and #6 onward
  hit the limiter. Every one of them is in the log either way.

**Eleven audit log entries from the run** (verbatim from `logs/audit.jsonl`;
the last four are rejections, two of them 429s):

```json
{"timestamp": "2026-11-08T01:30:16+00:00", "content_id": "28ff373f-7110-4d9a-bc60-99b84963f074", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.4, "combined_score": 0.3022, "label": "This looks like it was written by a person. Our automated check didn't find the patterns we usually see in AI-generated writing.", "status": "decided", "word_count": 45}
{"timestamp": "2026-11-08T01:30:14+00:00", "content_id": "01045165-d2ae-4d30-8413-172a5c9388c0", "creator_id": "attacker_EV05", "guess": "human", "model_score": 0.3212, "style_score": 0.3098, "combined_score": 0.3155, "label": "This looks like it was written by a person. Our automated check didn't find the patterns we usually see in AI-generated writing.", "status": "decided", "word_count": 82}
{"timestamp": "2026-11-08T01:30:14+00:00", "content_id": "35b4c5bd-ad37-40b4-84f1-5ac6dd0aea6a", "creator_id": "attacker_EV01", "guess": "unsure", "model_score": 0.1635, "style_score": 0.9857, "combined_score": 0.5746, "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.", "status": "decided", "word_count": 85}
{"timestamp": "2026-11-08T01:30:15+00:00", "content_id": "4f5c85da-552e-442f-87a6-fb4bd1f629d9", "creator_id": "attacker_EV10", "guess": "unsure", "model_score": 0.9792, "style_score": 0.2748, "combined_score": 0.627, "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.", "status": "decided", "word_count": 78}
{"timestamp": "2026-11-08T01:30:15+00:00", "content_id": "6e7870d4-fd61-45be-8f00-18380bffdc69", "creator_id": "attacker_FP03", "guess": "unsure", "model_score": 0.8051, "style_score": 0.5833, "combined_score": 0.6942, "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.", "status": "decided", "word_count": 83}
{"timestamp": "2026-11-08T01:30:16+00:00", "content_id": "e2b13e4a-8cc5-4bcc-81d3-c5cd3c86d255", "creator_id": "attacker_FP07", "guess": "unsure", "model_score": 0.8816, "style_score": 0.0, "combined_score": 0.4408, "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.", "status": "decided", "word_count": 59}
{"timestamp": "2026-11-08T01:30:16+00:00", "content_id": "cc5cb4e2-f78b-4810-abd0-6829d2b22ff8", "creator_id": "attacker_PI05", "guess": "unsure", "model_score": 0.6401, "style_score": 0.5715, "combined_score": 0.6058, "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.", "status": "decided", "word_count": 30}
{"timestamp": "2026-11-08T01:30:15+00:00", "creator_id": "attacker_EV08", "event": "rejected", "status": "rejected", "reason": "text_too_short", "route": "submit", "word_count": 10}
{"timestamp": "2026-11-08T01:30:16+00:00", "creator_id": "attacker_MF07", "event": "rejected", "status": "rejected", "reason": "text_too_short", "route": "submit", "word_count": 0}
{"timestamp": "2026-11-08T01:30:17+00:00", "creator_id": "attacker_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
{"timestamp": "2026-11-08T01:30:16+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

Why these: PI02 and EV05 are the two AI texts my system called **human**.
EV01 and EV10 show my two signals disagreeing completely (0.16 vs 0.99, and
0.98 vs 0.27). FP03 is the closest a real writer came to being accused.
FP07 shows a style score of exactly 0.0. PI05 shows the log injection landing
as a plain string. EV08 and MF07 are refusals, and MF07 is refused for the
wrong reason (see What's Still Broken). The last two are 429s: one from the
flood creator and one from the shared-address bucket.

**The single worst outcome:** FP03, a non-native English speaker writing
carefully. It scored **0.694** against an AI threshold of 0.70. The model
signal gave it 0.81, because careful, simple, textbook English is exactly what
GPT-2 finds easy to predict. It didn't get the AI label, but it was 0.006 away,
and the person it would hurt is the one least able to argue with the result.
A writer who learned English from textbooks writes like that on purpose. A
slightly plainer paragraph from the same person would have been accused, and
the label would have been telling them their careful writing looks fake.

---

## Run Log and Verdicts

`python run_eval.py --label before`, scored with `python score_eval.py
results/run_2026-11-07_1731_before.json`. `score_eval.py` applies each
criterion's rule from `criteria.md` to every trial, so I'm not counting by
hand. Its rules have their own tests (`tests/test_score_eval.py`).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human writing never labelled AI | 0 of 10 | 1/10 | 1/10 | 1/10 | **MISSED** |
| 2. AI and human score apart | gap ≥ 0.40 | 0.44 | 0.44 | 0.44 | **MET** |
| 3. All three labels reachable | 3 of 3 | 3/3 | 3/3 | 3/3 | **MET** |
| 4. Every appeal changes status and is logged | 10/10 + fake id 404 | 10/10, 404 | 10/10, 404 | 10/10, 404 | **MET** |
| 5. Bad input never crashes | 7/7 logged 4xx | 7/7 | 7/7 | 7/7 | **MET** |

**All three trials came out identical**, down to the fourth decimal. That's
expected: GPT-2 runs in eval mode with no sampling, and the style signal is
plain arithmetic. So the repeats show the result holds, not that it's noisy.

**Two earlier "before" runs are in `results/` too, and I didn't use them.** In
each one, a single request failed with `WinError 10055` ("the system lacked
sufficient buffer space") while *opening* the connection. Windows refused to
create a socket. The request never reached my service: there's no decision,
rejection or 429 for it in the log. So it was my test harness failing, not
any of the five stages. I added connect-only retries with backoff to
`run_eval.py` (safe for POST, because a connection that never opened sent
nothing), and the third run is clean. I kept the first two as evidence.

**What I tested with.** Criterion 1 and the human halves of 2 and 3 use
pre-2020 published prose copied exactly from Project Gutenberg (Douglass,
Baum, Thoreau, Austen, Melville, Franklin, London, Doyle, Riis, Jerome). None
of it is from my calibration set. My criterion says "my own writing plus
published prose", and I only used published prose, so criterion 1 was tested
on other people's writing, not mine. The AI texts were generated with Claude
for this test. Criterion 4 needs a real `content_id`, so I extended
`run_eval.py` to appeal each submission and check `/content/<id>` and the log
afterwards. Criterion 5 needs exactly one log entry per bad request, so
`run_eval.py` now reads the log size from `/health` before and after every
request.

**Real output, trial 1** of `results/run_2026-11-07_1731_before.json`, produced
by `run_eval.py::main` against `app.py::submit` (scoring in
`scoring.py::combine_signals`). Label text and `sent` are cut short here; the
file has them in full.

#### Criterion 1. human writing
```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6206,
    "model_score": 0.6081,
    "style_score": 0.6331,
    "label": "We can't tell whether this was written by a person or with h...",
    "error": null,
    "log_delta": 1,
    "sent": "The colonel, after ascertaining where the slave belonged, ro"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7372,
    "model_score": 0.7425,
    "style_score": 0.732,
    "label": "This reads a lot like AI-generated writing. Automated checks...",
    "error": null,
    "log_delta": 1,
    "sent": "They now came upon more and more of the big scarlet poppies,"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2581,
    "model_score": 0.3536,
    "style_score": 0.1626,
    "label": "This looks like it was written by a person. Our automated ch...",
    "error": null,
    "log_delta": 1,
    "sent": "With a little more deliberation in the choice of their pursu"
  }
]
```
#### Criterion 2. score spread
```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8699,
    "model_score": 0.7702,
    "style_score": 0.9695,
    "label": "This reads a lot like AI-generated writing. Automated checks...",
    "error": null,
    "log_delta": 1,
    "sent": "Remote work has fundamentally transformed the way organizati"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7231,
    "model_score": 0.6027,
    "style_score": 0.8435,
    "label": "This reads a lot like AI-generated writing. Automated checks...",
    "error": null,
    "log_delta": 1,
    "sent": "When I glance over my notes and records of the Sherlock Holm"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2714,
    "model_score": 0.356,
    "style_score": 0.1869,
    "label": "This looks like it was written by a person. Our automated ch...",
    "error": null,
    "log_delta": 1,
    "sent": "These figures speak for themselves, when it is shown that in"
  }
]
```
#### Criterion 3. label coverage
```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8699,
    "model_score": 0.7702,
    "style_score": 0.9695,
    "label": "This reads a lot like AI-generated writing. Automated checks...",
    "error": null,
    "log_delta": 1,
    "sent": "Remote work has fundamentally transformed the way organizati"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2456,
    "model_score": 0.4029,
    "style_score": 0.0883,
    "label": "This looks like it was written by a person. Our automated ch...",
    "error": null,
    "log_delta": 1,
    "sent": "The works of the great poets have never yet been read by man"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.35,
    "model_score": 0.6298,
    "style_score": 0.0594,
    "label": "We can't tell whether this was written by a person or with h...",
    "error": null,
    "log_delta": 1,
    "sent": "Mr. Gore was a grave man, and, though a young man, he indulg"
  }
]
```
#### Criterion 4. appeal path
```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7372,
    "model_score": 0.7425,
    "style_score": 0.732,
    "label": "This reads a lot like AI-generated writing. Automated checks...",
    "error": null,
    "log_delta": 1,
    "sent": "They now came upon more and more of the big scarlet poppies,",
    "appeal_status": 200,
    "appeal_body_status": "under_review",
    "status_after": "under_review",
    "appeal_entries": 1,
    "original_decision_intact": true
  },
  {
    "sent": "appeal against a made-up content_id",
    "appeal_status": 404,
    "appeal_entries": 0
  }
]
```
#### Criterion 5. bad input
```json
[
  {
    "status": 400,
    "guess": null,
    "error": "invalid_text",
    "log_delta": 1,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "guess": null,
    "error": "invalid_text",
    "log_delta": 1,
    "sent": "{\"creator_id\": \"eval_bad_missing\"}"
  },
  {
    "status": 413,
    "guess": null,
    "error": "text_too_long",
    "log_delta": 1,
    "sent": "word word word word word word word word word word word word "
  },
  {
    "status": 400,
    "guess": null,
    "error": "invalid_creator_id",
    "log_delta": 1,
    "sent": "{\"text\": \"At Burlington I made an acquaintance with many pri"
  }
]
```

**How I decided each verdict**

1. **MISSED.** One of ten got the AI label in all three trials, and the target
   was zero. The Wizard of Oz passage scored 0.737.
2. **MET.** The gap was 0.44 in every trial against a target of 0.40. It's not
   a comfortable margin, and a Doyle passage in the human group scored 0.72,
   which is the same bug as criterion 1.
3. **MET.** Each label showed up in every trial. The "human" label came from
   one input only (Thoreau, 0.246), which matters later.
4. **MET.** 10 of 10 appeals returned 200 and `under_review`, each added exactly
   one appeal entry, the decision entry stayed, and the made-up id got a 404
   with no appeal entry. All three trials.
5. **MET.** All 7 bad bodies got a JSON 4xx (six 400s and a 413 for the
   50,000-word text) and exactly one new log entry each.

**Diagnoses**

*Criterion 1 miss. Stage: signal two. Mechanism: a spread measured from too few
sentences.* The passage that got the AI label is three long sentences from The
Wizard of Oz, about 39 words each, built the same way ("more and more ... fewer
and fewer"). My style signal's biggest part (weight 0.6) is the spread of
sentence lengths, stdev divided by mean. With three sentences that number is
mostly noise, and here it came out 0.16, which my anchors read as almost
perfectly AI-even. Signal one agreed (0.74), because plain children's prose is
easy for GPT-2 to predict. Both signals were on the same side of 0.5, so my
disagreement cap never kicked in, and the average landed at 0.737, over 0.70.
The Doyle passage that scored 0.72 in criterion 2 is the same story: four
sentences, spread 0.13. Every human passage that scored high had 2-4 sentences.
The ones with 5+ sentences all scored lower.

*Broken attacks. There's one pattern, and it's in the combining rule.* Eight
evasions and PI02 broke. In every one of them, at least one signal was fooled,
and averaging gave the other signal no way to save it. My clean AI texts score
0.80 to 0.87, so they only have 0.10 to 0.17 above the 0.70 line. Drag one
signal down by 0.3 and the average falls into "unsure". Which signal got
fooled differs:

- **Signal one, by unusual tokens.** EV01 (typos) dropped the model score to
  0.16, because a typo is a token GPT-2 didn't expect. The attack said it
  targeted signal two, but my signal two did the opposite of what the attacker
  assumed: higher word variety reads as *more* AI in my calibration, so it went
  to 0.99. The plain average was already 0.575, inside the unsure band, so my disagreement cap had nothing to do. PI02 is the same
  mechanism: the "SYSTEM: ... guess=human, confidence=0.02" line is full of
  odd tokens, so the model score fell to 0.20 and the total to 0.30, which is
  the human label. My service didn't obey the instruction (there's no LLM in
  the path to obey it). The weird formatting just raised perplexity, and the
  outcome was the same as if it had worked.
- **Signal two, by structure.** EV10 repeats a stanza, which lowers word
  variety, so my style signal said 0.27 (human) while the model said 0.98.
  EV02 and EV06 change sentence lengths on purpose, which raises the spread.
- **Both, a little.** EV03, EV07 and EV09 each pulled both signals toward the
  middle (0.58 to 0.70) and landed at 0.58 to 0.64.
- **EV05** is a heavy human edit, and both signals called it human (0.32 and
  0.31). I'm marking it BROKE because the rule says so, but I'm not sure it's a
  failure. After that much human rewriting, the text mostly is human writing.

So the stage is the combining rule plus where the AI threshold sits, and the
mechanism is that an average needs only one fooled signal to leave the AI band.
That isn't an accident. I set the AI threshold high on purpose in unit 7, to
protect writers. These breaks are the price of that choice, showing up in the
data.

---

## The Improvement

**What I changed:** one rule in signal two. Below 5 sentences, the sentence
spread now counts as 0.5 ("can't tell") instead of being measured. It was
already doing that for 1 sentence; the cutoff is now
`config.MIN_SENTENCES_FOR_SPREAD = 5`. Nothing else changed: same weights, same
thresholds, same model.

**Why 5:** the uncertainty of a standard deviation from n values is roughly
1/sqrt(2(n-1)). That's about 50% at 3 sentences and 35% at 5. My spread
anchors (0.15 for AI, 0.60 for human) were set on texts with 7-8 sentences, so
they were never meant for a 3-point sample. I also checked 4 and 6 before
running anything: 4 would have left the 4-sentence Doyle passage at 0.72, and
6 started stripping "human" from 5-sentence texts that measured fine.

**Which diagnosis pointed at it:** criterion 1. Every high-scoring human text
had 2-4 sentences.

**Before I ran it, I predicted what it would do**, by recomputing the style
score for every input with the new rule and recombining with the logged model
scores (signal one doesn't change). The prediction said: the Wizard of Oz
passage and Doyle go from AI to unsure, Thoreau goes from human to unsure, and
no attack changes its label. That's exactly what the re-run did. I also looked
at the other choice, raising the AI threshold to 0.75. It would have fixed
criterion 1 without costing criterion 3, but Baum would have cleared it by
0.013, and it treats the symptom. The next plain three-sentence paragraph at
0.76 would get accused again.

### Run Log — After

`python run_eval.py --label after`, `results/run_2026-11-07_1739_after.json`.

| Criterion | Target | Before (×3) | Run 1 | Run 2 | Run 3 | Verdict before → after |
|---|---|---|---|---|---|---|
| 1. Human writing never labelled AI | 0 of 10 | 1/10 | 0/10 | 0/10 | 0/10 | MISSED → **MET** |
| 2. AI and human score apart | gap ≥ 0.40 | 0.44 | 0.47 | 0.47 | 0.47 | MET → **MET** |
| 3. All three labels reachable | 3 of 3 | 3/3 | 2/3 (no human) | 2/3 | 2/3 | MET → **MISSED** |
| 4. Every appeal changes status and is logged | 10/10 + 404 | 10/10 | 10/10 | 10/10 | 10/10 | MET → **MET** |
| 5. Bad input never crashes | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 | MET → **MET** |

The pieces that moved, from the same files:

| Input | Sentences | Before | After |
|---|---|---|---|
| Baum, Wizard of Oz (criterion 1) | 3 | 0.737 **ai** | 0.591 unsure |
| Doyle, notes passage (criterion 2, human group) | 4 | 0.723 **ai** | 0.573 unsure |
| Thoreau, Walden (criterion 3, formal human) | 3 | 0.246 **human** | 0.396 unsure |
| Doyle, "strange and impressive figure" (criterion 1) | 4 | 0.388 unsure | 0.516 unsure |
| Jerome, Three Men in a Boat (criterion 1) | 2 | 0.517 unsure | 0.367 unsure |

### Attack Run — After

`python run_attacks.py --set attack_set/attack_set --label after`,
`results/attack_run_2026-11-07_1739_after.md`.

| ID | Targeting | Before | After | Verdict before / after |
|---|---|---|---|---|
| EV01 | signal two: typos raise word variety | 200 unsure 0.575 (m 0.16, s 0.99) | 200 unsure 0.575 (m 0.16, s 0.99) | BROKE / BROKE |
| EV02 | signal two: broken-up sentences raise length spread | 200 unsure 0.491 (m 0.59, s 0.39) | 200 unsure 0.491 (m 0.59, s 0.39) | BROKE / BROKE |
| EV03 | signal two: a pasted quotation changes the shape | 200 unsure 0.637 (m 0.67, s 0.61) | 200 unsure 0.637 (m 0.67, s 0.61) | BROKE / BROKE |
| EV04 | signal one: unusual words raise perplexity | 200 ai 0.790 (m 0.61, s 0.97) | 200 ai 0.790 (m 0.61, s 0.97) | HELD / HELD |
| EV05 | both signals: heavy human editing pass | 200 human 0.316 (m 0.32, s 0.31) | 200 human 0.316 (m 0.32, s 0.31) | BROKE / BROKE |
| EV06 | signal two: one very long sentence and one very short | 200 unsure 0.429 (m 0.57, s 0.29) | 200 unsure 0.429 (m 0.57, s 0.29) | BROKE / BROKE |
| EV07 | signal two: padding with punctuation | 200 unsure 0.583 (m 0.59, s 0.58) | 200 unsure 0.583 (m 0.59, s 0.58) | BROKE / BROKE |
| EV08 | signal one: text below the token window | 400 | 400 | HELD / HELD |
| EV09 | both: AI text with a human opening paragraph bolted on | 200 unsure 0.640 (m 0.70, s 0.58) | 200 unsure 0.640 (m 0.70, s 0.58) | BROKE / BROKE |
| EV10 | signal two: repeated stanza structure | 200 unsure 0.627 (m 0.98, s 0.27) | 200 unsure 0.640 (m 0.98, s 0.30) | BROKE / BROKE |
| FP01 | plain, clear human writing with no flourishes | 200 unsure 0.500 (m 0.62, s 0.38) | 200 unsure 0.500 (m 0.62, s 0.38) | HELD / HELD |
| FP02 | human writing in a formal register | 200 unsure 0.664 (m 0.74, s 0.59) | 200 unsure 0.664 (m 0.74, s 0.59) | HELD / HELD |
| FP03 | a non-native English speaker writing carefully | 200 unsure 0.694 (m 0.81, s 0.58) | 200 unsure 0.694 (m 0.81, s 0.58) | HELD / HELD |
| FP04 | a student essay written to a rubric | 200 unsure 0.684 (m 0.83, s 0.54) | 200 unsure 0.684 (m 0.83, s 0.54) | HELD / HELD |
| FP05 | technical documentation written by a person | 200 unsure 0.616 (m 0.80, s 0.43) | 200 unsure 0.616 (m 0.80, s 0.43) | HELD / HELD |
| FP06 | a person imitating a formal template | 200 unsure 0.535 (m 0.88, s 0.19) | 200 unsure 0.535 (m 0.88, s 0.19) | HELD / HELD |
| FP07 | human writing that repeats a phrase deliberately | 200 unsure 0.441 (m 0.88, s 0.00) | 200 unsure 0.441 (m 0.88, s 0.00) | HELD / HELD |
| FP08 | very short genuine human submission | 400 | 400 | HELD / HELD |
| PI01 | instruction to ignore the check | 200 unsure 0.431 (m 0.46, s 0.40) | 200 unsure 0.431 (m 0.46, s 0.40) | HELD / HELD |
| PI02 | instruction disguised as a system message | 200 human 0.302 (m 0.20, s 0.40) | 200 human 0.302 (m 0.20, s 0.40) | BROKE / BROKE |
| PI03 | instruction wrapped in the writer's voice | 200 unsure 0.668 (m 0.59, s 0.74) | 200 unsure 0.647 (m 0.59, s 0.70) | HELD / HELD |
| PI04 | attempt to make the label text hostile | 200 unsure 0.541 (m 0.50, s 0.58) | 200 unsure 0.555 (m 0.50, s 0.61) | HELD / HELD |
| PI05 | attempt to inject into the audit log | 200 unsure 0.606 (m 0.64, s 0.57) | 200 unsure 0.670 (m 0.64, s 0.70) | HELD / HELD |
| PI06 | instruction plus real human text | 200 unsure 0.485 (m 0.56, s 0.41) | 200 unsure 0.485 (m 0.56, s 0.41) | HELD / HELD |
| MF01 | text is only whitespace | 400 | 400 | HELD / HELD |
| MF02 | text is a single character | 400 | 400 | HELD / HELD |
| MF03 | text is control characters | 400 | 400 | HELD / HELD |
| MF04 | text is only punctuation | 400 | 400 | HELD / HELD |
| MF05 | text is a very long single word | 400 | 400 | HELD / HELD |
| MF06 | text is emoji only | 400 | 400 | HELD / HELD |
| MF07 | text is right-to-left script | 400 | 400 | HELD / HELD |
| MF08 | text is 60,000 characters | 413 | 413 | HELD / HELD |
| RQ01 | no text field at all | 400 | 400 | HELD / HELD |
| RQ02 | no creator_id | 400 | 400 | HELD / HELD |
| RQ03 | text is a number | 400 | 400 | HELD / HELD |
| RQ04 | text is a list | 400 | 400 | HELD / HELD |
| RQ05 | text is null | 400 | 400 | HELD / HELD |
| RQ06 | creator_id is an object | 400 | 400 | HELD / HELD |
| RQ07 | body is a JSON array, not an object | 429 | 429 | HELD / HELD |
| RQ08 | body is unparseable JSON | 429 | 429 | HELD / HELD |
| RQ09 | body is empty | 429 | 429 | HELD / HELD |
| RQ10 | body is form-encoded, not JSON | 429 | 429 | HELD / HELD |
| RQ11 | body is JSON claiming to be plain text | 429 | 429 | HELD / HELD |
| RQ12 | deeply nested JSON | 400 | 400 | HELD / HELD |
| FL01_01 | 20 rapid submissions from one creator | 400 | 400 | HELD / HELD |
| FL01_02 | 20 rapid submissions from one creator | 400 | 400 | HELD / HELD |
| FL01_03 | 20 rapid submissions from one creator | 400 | 400 | HELD / HELD |
| FL01_04 | 20 rapid submissions from one creator | 400 | 400 | HELD / HELD |
| FL01_05 | 20 rapid submissions from one creator | 400 | 400 | HELD / HELD |
| FL01_06 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_07 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_08 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_09 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_10 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_11 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |
| FL01_12 | 20 rapid submissions from one creator | 429 | 429 | HELD / HELD |

**After: 47 held, 9 broke, out of 56.** (Before: 47 held, 9 broke.)

No attack changed its label or its verdict. Four scores moved inside the unsure
band (EV10 0.627 to 0.640, PI03, PI04, PI05), all short texts where the spread
is now neutral. RQ07 to RQ11 hit the address limit again, the same as before.

**Did it help, and how do I know:** yes for what it aimed at, and it cost me a
criterion. Criterion 1 went from 1/10 to 0/10 in all three trials, and the
criterion 2 gap got wider (0.44 to 0.47). But criterion 3 went from MET to
MISSED. Its only "human" result was Thoreau, and that label was also resting on
a three-sentence spread. The fix took away the false confidence in both
directions, which is what I wanted, but it means the human label now needs
real evidence from both signals. It's still reachable (four criterion 1 texts
get it after the fix), just not by anything in criterion 3's set. I'm not
going to swap Thoreau for a longer passage so it passes. That would be changing
the test to fit the result. The evasion attacks didn't get better or worse,
which matches the diagnosis: they break in the combining rule, and I didn't
touch it.

---

## What's Still Broken

- **Criterion 3 (MISSED after the fix).** I'd look at why plain human prose
  with 5+ sentences rarely goes below 0.35. Douglass's plain passage sits at
  exactly 0.35, which counts as unsure because both boundaries belong to that
  band. The likely next step is checking the vocabulary anchors on more than
  six calibration texts, since that's now carrying short texts alone. I stopped
  because the unit allows one measured change, and moving the human threshold
  just to win back one label is the same kind of symptom fix I turned down for
  criterion 1.
- **Eight evasions and PI02 (all still BROKE).** Two things I'd try. First, a
  disagreement rule that sends "one signal very sure, the other fooled" to a
  human reviewer instead of just "unsure". That catches EV01, EV10 and PI02's
  pattern without accusing anyone automatically. Second, cleaning text before
  signal one: drop lines that look like instructions or system prompts and
  fix obvious typos before GPT-2 reads it. I stopped because each of those
  changes signal one or the combining rule for every writer, and I'd need to
  re-run criterion 1 and the false-positive attacks to show they don't push
  real writing up. Typos are human too.
- **FP03 at 0.694.** Not broken, but close. The real fix is a model signal that
  isn't GPT-2 perplexity, because predictable English is what careful
  non-native writers produce. I can't fix that inside this unit.
- **MF07 (right-to-left script) is refused for the wrong reason.** It gets 400
  `text_too_short` with `word_count: 0`, because `stylometry.words` only
  matches a-z and 0-9. The refusal itself is right (GPT-2 here is an English
  model), but telling an Arabic or Hebrew writer their text is "too short" is
  wrong. A separate `unsupported_language` reason would fix the message. I left
  it because it doesn't change any outcome, only the wording.
- **A script that rotates `creator_id`s isn't rate limited at all.** That's the
  per-creator trade from the Rate Limiting section. It needs real accounts.

**The trade I'd make if this ran for real:** I'd keep the AI label hard to
reach and accept that more AI text gets through as "unsure", which this unit
showed is what happens (seven evasions landed there, and EV05 even got "human"). The people who pay are
the honest writers competing with AI-assisted pieces on the same site, and a
moderator who has to read more unsure cases by hand, but that cost is spread
out and recoverable, while a false accusation lands on one writer, FP03's
writer for example, and sticks.


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

       [x] Rate limiting on /submit, with your numbers justified
       [x] The pasted run of status codes showing 429
       [x] Audit log with all nine fields, recording rejections too
       [x] The attack set run IN FULL, every input with an outcome
       [x] Ten audit log entries pasted as text
       [x] Five criteria across three trials
       [x] A diagnosis for every miss and every broken attack — stage AND mechanism
       [x] One improvement, with Attack Run — After
       [x] What's Still Broken, including the production trade
       [x] At least four new commits
       [x] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

---

<!-- ═══════════════════════ UNIT 9 — CAPSTONE ═══════════════════════ -->

## Capstone

### The System

I'm extending Provenance Guard, this repo, the Flask service that scores a
piece of writing with two signals (GPT-2 perplexity and a style measure),
labels it human, unsure or AI, and lets the writer appeal. I picked it over my
other three because it's the one whose weak points I know best: I spent unit 8
attacking it, and I already know where its time goes (GPT-2) and where its
logging had gaps.

### The Shape

**Shape A, deploy and instrument.** Until now this only ran as `python app.py`,
Flask's development server, started by hand, with an audit log that recorded
decisions but not how long anything took or what it cost. What I'm adding:

- a real run path: `python serve.py`, one command that loads the model first and
  then serves through `waitress` (a production WSGI server that works on
  Windows, unlike gunicorn);
- instrumentation on every request, including the failed ones: a request id,
  the route, the HTTP status, wall time, CPU time, the size and a fingerprint of
  the input, and for scored submissions the time spent in each stage (GPT-2,
  style signal, scoring);
- a handler that logs and answers in JSON when something crashes, instead of a
  bare HTML 500 with no record;
- `ops_report.py`, which reads the log back and prints latency percentiles, the
  per-stage breakdown and CPU seconds per request, and `ops_eval.py`, which
  starts the server fresh and runs my five criteria three times.

This is Path B, local with logs. The arithmetic is in RUNNING.md: torch plus
the GPT-2 weights need more than the 512 MB a free host gives.

### Out of Scope

- **No hosting.** I'm not trying to squeeze this onto a free tier by swapping
  GPT-2 for a smaller model. That would change signal one, and every threshold
  I calibrated in unit 7 would need redoing.
- **No changes to the detector's decisions.** The signals, the combining rule
  and the thresholds stay exactly as unit 8 left them. The "send disagreements
  to a human" idea from What's Still Broken is a scoring change, not an
  operations one.
- **No dashboard.** The numbers come out of a script that reads the log. A web
  page for them would be a second project.

### Stretch

Only the **latency breakdown** (time per stage of one run, measured). The stage
timers are part of the instrumentation anyway, so it costs me a few lines in
the report. I'm skipping the load test, the second improvement and the second
run path.

### Instrumentation

Every request to `/submit` and `/appeal` writes one JSON line to
`logs/audit.jsonl`, and so does every start of `serve.py`. The fields I added
for the capstone (`app.py::_ops`, `app.py::_start_clock`):

| Field | What it is |
|---|---|
| `request_id` | 12 hex characters, also sent back in the `X-Request-ID` response header |
| `route`, `http_status` | where the request went and what it got back |
| `input_bytes` | size of the request body, so even a rejected request says what came in |
| `duration_ms` | wall time from the start of the request to the log write |
| `cpu_ms` | process CPU time over the same span (Windows counts it in 15.6 ms ticks, so small requests show 0.0) |
| `input_chars`, `input_sha256` | scored submissions only: text length and a fingerprint, so the same text can be found again without storing it twice |
| `model_ms`, `style_ms`, `score_ms` | scored submissions only: time in GPT-2, the style signal, and combining plus labelling |

The original nine fields (timestamp, content_id, creator_id, guess, the three
scores, label, status) are unchanged. Timestamps now have milliseconds.

**Extract from a real session** (the smoke run on 2026-11-13, `python
ops_eval.py --label smoke --trials 1`). I cut the `label` sentence short on the
scored lines so they fit; everything else is as written.

```json
{"timestamp": "2026-11-14T06:34:55.357+00:00", "event": "startup", "model": "gpt2", "model_load_s": 23.99, "host": "127.0.0.1", "port": 5055, "threads": 4, "python": "3.11.9", "rate_limiting": true}
{"timestamp": "2026-11-14T06:34:57.949+00:00", "content_id": "7ad7fc71-806c-4b40-9b71-f2fb265f4c9c", "creator_id": "ops-smoke-t1-223430-h0", "guess": "unsure", "model_score": 0.6081, "style_score": 0.6331, "combined_score": 0.6206, "label": "We can't tell whether this was written b...", "status": "decided", "word_count": 124, "input_chars": 700, "input_sha256": "1c9cf237f4ab61f4", "model_ms": 2031.2, "style_ms": 1.9, "score_ms": 0.0, "request_id": "6e6ae5cddec3", "route": "/submit", "http_status": 200, "input_bytes": 757, "duration_ms": 2036.6, "cpu_ms": 12859.4}
{"timestamp": "2026-11-14T06:34:58.456+00:00", "content_id": "6fb38532-5712-49f1-990c-7316c9a8518f", "creator_id": "ops-smoke-t1-223430-h1", "guess": "unsure", "model_score": 0.7425, "style_score": 0.4391, "combined_score": 0.5908, "label": "We can't tell whether this was written b...", "status": "decided", "word_count": 118, "input_chars": 611, "input_sha256": "672557c9d09aba7b", "model_ms": 494.3, "style_ms": 1.0, "score_ms": 0.0, "request_id": "551c136313e5", "route": "/submit", "http_status": 200, "input_bytes": 663, "duration_ms": 498.5, "cpu_ms": 3796.9}
{"timestamp": "2026-11-14T06:34:59.024+00:00", "content_id": "2611ada0-5aa0-4b5a-bbd3-eab95d6fc540", "creator_id": "ops-smoke-t1-223430-h2", "guess": "human", "model_score": 0.3536, "style_score": 0.1626, "combined_score": 0.2581, "label": "This looks like it was written by a pers...", "status": "decided", "word_count": 158, "input_chars": 878, "input_sha256": "d9697917da19b74b", "model_ms": 555.3, "style_ms": 1.6, "score_ms": 0.0, "request_id": "5a39b4db3fe4", "route": "/submit", "http_status": 200, "input_bytes": 930, "duration_ms": 560.0, "cpu_ms": 4359.4}
{"timestamp": "2026-11-14T06:34:59.752+00:00", "content_id": "278b5642-e73a-474f-ab75-b4cc869b9cd3", "creator_id": "ops-smoke-t1-223430-h3", "guess": "human", "model_score": 0.5308, "style_score": 0.1498, "combined_score": 0.3403, "label": "This looks like it was written by a pers...", "status": "decided", "word_count": 200, "input_chars": 1102, "input_sha256": "e0858b8f39b2bfed", "model_ms": 713.9, "style_ms": 2.1, "score_ms": 0.0, "request_id": "1023cd27abe3", "route": "/submit", "http_status": 200, "input_bytes": 1164, "duration_ms": 719.1, "cpu_ms": 4859.4}
{"timestamp": "2026-11-14T06:35:01.092+00:00", "content_id": "91475fcc-bc42-4837-85f7-f1123ddada5e", "creator_id": "ops-smoke-t1-223430-h5", "guess": "unsure", "model_score": 0.429, "style_score": 0.7183, "combined_score": 0.5736, "label": "We can't tell whether this was written b...", "status": "decided", "word_count": 145, "input_chars": 841, "input_sha256": "210d654f459d222f", "model_ms": 574.3, "style_ms": 1.5, "score_ms": 0.0, "request_id": "219f6928f553", "route": "/submit", "http_status": 200, "input_bytes": 893, "duration_ms": 578.7, "cpu_ms": 3968.8}
{"timestamp": "2026-11-14T06:35:05.903+00:00", "content_id": "7ad7fc71-806c-4b40-9b71-f2fb265f4c9c", "creator_id": "ops-smoke-t1-223430-h0", "event": "appeal", "status": "under_review", "reasoning": "I wrote this myself.", "request_id": "d1b30bcc6111", "route": "/appeal", "http_status": 200, "input_bytes": 91, "duration_ms": 40.2, "cpu_ms": 31.2}
{"timestamp": "2026-11-14T06:35:05.912+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "invalid_json", "request_id": "009a50ad066f", "route": "submit", "http_status": 400, "input_bytes": 16, "duration_ms": 2.3, "cpu_ms": 0.0}
{"timestamp": "2026-11-14T06:35:05.939+00:00", "creator_id": "ops-smoke-t1-223430-b3", "event": "rejected", "status": "rejected", "reason": "text_too_long", "request_id": "eaeb8ae2be24", "route": "submit", "http_status": 413, "input_bytes": 20053, "duration_ms": 1.1, "cpu_ms": 0.0, "text_length": 20001}
{"timestamp": "2026-11-14T06:35:05.986+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "request_too_large", "request_id": "666e2c45d0cd", "route": "/submit", "http_status": 413, "input_bytes": 1100012, "duration_ms": 0.8, "cpu_ms": 0.0}
{"timestamp": "2026-11-14T06:35:06.032+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "not_found", "request_id": "2226aaeddead", "route": "appeal", "http_status": 404, "input_bytes": 84, "duration_ms": 38.2, "cpu_ms": 15.6, "requested_content_id": "00000000-0000-4000-8000-000000000000"}
{"timestamp": "2026-11-14T06:35:06.088+00:00", "creator_id": "ops-smoke-t1-223430-flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute", "request_id": "99ee45e5abcc", "route": "/submit", "http_status": 429, "input_bytes": 77, "duration_ms": 0.9, "cpu_ms": 0.0}
```

The last five lines are failed runs: bad JSON, a text over 20,000 characters,
a 1.1 MB body, an appeal for an id that was never issued, and a rate-limited
submission. Each one has a request id, a status and a duration, so a failure
shows up as a line and not as a gap.

A crash inside a route didn't happen in this session, so it isn't in the
extract. `tests/test_instrumentation.py::test_a_crash_answers_json_500_and_leaves_a_log_line`
forces one (GPT-2 raising `RuntimeError`) and checks that the client gets a
JSON 500 and the log gets a line with `reason: internal_error`,
`event_detail: RuntimeError` and `http_status: 500`. Before this unit that
same crash gave Flask's HTML error page and nothing in the log.

Two things I noticed just from reading these lines. The first submission after
a start took 2,037 ms while the rest took about 500 to 700 ms, so the first
real request pays a one-off cost that loading the model doesn't cover. And the
two appeals take about 40 ms when a rejection takes 1 to 3 ms, because
`/appeal` reads the whole log file to find the original decision. That grows
with the log.

### What It Costs

There's no API bill. GPT-2 runs on my own CPU, so the real cost of one run is
compute: CPU-seconds, and how long a writer waits.

**How I measured it:** each scored submission logs `cpu_ms`, the change in
`time.process_time()` across the request. That counts CPU time on every
thread in the process, including torch's own worker threads, so it's only
exact when requests don't overlap, and `ops_eval.py` sends them one at a time.
I ran the smoke session (15 real submissions) and then `python ops_report.py
--last 10`, which averages the last ten scored submissions in the log:

```
Scored submissions: 10  (2026-11-14T06:35:01.092+00:00 to 2026-11-14T06:35:05.855+00:00)
  wall ms   mean   526.9  p50   500.8  p95   676.4  max   676.4
  CPU ms    mean  4300.0  p50  3968.8  p95  5765.6  max  5765.6
  CPU / wall: 8.2 cores busy on average

Where the time goes (mean ms per scored submission):
  GPT-2 (signal one)     522.6  (99.2%)
  style (signal two)       1.4  ( 0.3%)
  combine + label          0.0  ( 0.0%)
  validation + log         2.9  ( 0.5%)
```

**Measured cost of one run, before any changes: 4.3 CPU-seconds and 0.53
seconds of wall time.** Rejected requests cost close to nothing (0.8 to 3 ms,
under one 15.6 ms CPU tick). Starting the service costs a one-off 24 to 67
seconds of model loading, and the process holds about 1 GB of memory once it
has scored something.

The number that surprised me is the ratio. Half a second of waiting burns more
than four seconds of CPU, which means torch is spreading one small GPT-2
forward pass across about eight cores at once. That's what criterion C4 is
about.
