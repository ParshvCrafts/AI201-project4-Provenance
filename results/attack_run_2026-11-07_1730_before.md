# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-07 17:30
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `35b4c5bd-ad37-40b4-84f1-5ac6dd0aea6a` | unsure | 0.575 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `2f868b25-33ef-4593-8c5e-ac4b2856da3d` | unsure | 0.491 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `fc088a1d-6ed9-4ce1-9b33-004a01f45b5c` | unsure | 0.637 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `bb57c135-a1c7-4b05-9241-20d00f1e2079` | ai | 0.790 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `01045165-d2ae-4d30-8413-172a5c9388c0` | human | 0.316 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `7881d641-2eb5-43f7-86d2-36fcf14cfad2` | unsure | 0.429 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `62775b75-8a9e-4a80-af17-0dec05369d17` | unsure | 0.583 |  |
| EV08 | evasion | signal one: text below the token window | 400 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `0633efe1-b738-4884-8fff-7b9a4495f8eb` | unsure | 0.640 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `4f5c85da-552e-442f-87a6-fb4bd1f629d9` | unsure | 0.627 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `42e56a9c-ffb0-4f7a-8bb2-e55879908c02` | unsure | 0.500 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `30e8613c-e42f-478f-aac5-88055795d6a9` | unsure | 0.664 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `6e7870d4-fd61-45be-8f00-18380bffdc69` | unsure | 0.694 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `a3e6e691-808f-465f-b78a-004dd24747d8` | unsure | 0.684 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `a7a6d5ad-edd7-46e4-abf0-c1aded544edd` | unsure | 0.616 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `5c3bf5d9-19d0-475e-9540-09cefaf80e5f` | unsure | 0.535 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `e2b13e4a-8cc5-4bcc-81d3-c5cd3c86d255` | unsure | 0.441 |  |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `cb707ade-06a9-4322-bc24-4b1a88fe8678` | unsure | 0.431 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `28ff373f-7110-4d9a-bc60-99b84963f074` | human | 0.302 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `5322bfaf-49c4-4769-85f1-ac4cccf71190` | unsure | 0.668 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `0bb05eb6-e988-4a5c-8d8f-f67677be9334` | unsure | 0.541 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `cc5cb4e2-f78b-4810-abd0-6829d2b22ff8` | unsure | 0.606 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `d3427a8b-c633-4f69-a6f9-208c0c0d40e9` | unsure | 0.485 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 429 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 429 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 429 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "35b4c5bd-ad37-40b4-84f1-5ac6dd0aea6a",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.5746,
  "model_score": 0.1635,
  "style_score": 0.9857,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "2f868b25-33ef-4593-8c5e-ac4b2856da3d",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.4908,
  "model_score": 0.5943,
  "style_score": 0.3873,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "fc088a1d-6ed9-4ce1-9b33-004a01f45b5c",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6375,
  "model_score": 0.6662,
  "style_score": 0.6088,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "bb57c135-a1c7-4b05-9241-20d00f1e2079",
  "creator_id": "attacker_EV04",
  "guess": "ai",
  "confidence": 0.7897,
  "model_score": 0.6114,
  "style_score": 0.968,
  "label": "This reads a lot like AI-generated writing. Automated checks like ours can be wrong, so if you wrote this yourself, you can ask for a person to review it.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "01045165-d2ae-4d30-8413-172a5c9388c0",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.3155,
  "model_score": 0.3212,
  "style_score": 0.3098,
  "label": "This looks like it was written by a person. Our automated check didn't find the patterns we usually see in AI-generated writing.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "7881d641-2eb5-43f7-86d2-36fcf14cfad2",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4295,
  "model_score": 0.5727,
  "style_score": 0.2863,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "62775b75-8a9e-4a80-af17-0dec05369d17",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5825,
  "model_score": 0.5862,
  "style_score": 0.5787,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "0633efe1-b738-4884-8fff-7b9a4495f8eb",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.6404,
  "model_score": 0.7042,
  "style_score": 0.5766,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "4f5c85da-552e-442f-87a6-fb4bd1f629d9",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.627,
  "model_score": 0.9792,
  "style_score": 0.2748,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "42e56a9c-ffb0-4f7a-8bb2-e55879908c02",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.4997,
  "model_score": 0.6175,
  "style_score": 0.3818,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "30e8613c-e42f-478f-aac5-88055795d6a9",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.6643,
  "model_score": 0.7387,
  "style_score": 0.5898,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "6e7870d4-fd61-45be-8f00-18380bffdc69",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.6942,
  "model_score": 0.8051,
  "style_score": 0.5833,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "a3e6e691-808f-465f-b78a-004dd24747d8",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.6843,
  "model_score": 0.8329,
  "style_score": 0.5357,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "a7a6d5ad-edd7-46e4-abf0-c1aded544edd",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.6157,
  "model_score": 0.8005,
  "style_score": 0.4308,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "5c3bf5d9-19d0-475e-9540-09cefaf80e5f",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.5346,
  "model_score": 0.8814,
  "style_score": 0.1878,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "e2b13e4a-8cc5-4bcc-81d3-c5cd3c86d255",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.4408,
  "model_score": 0.8816,
  "style_score": 0.0,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "cb707ade-06a9-4322-bc24-4b1a88fe8678",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.4313,
  "model_score": 0.4625,
  "style_score": 0.4,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "28ff373f-7110-4d9a-bc60-99b84963f074",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.3022,
  "model_score": 0.2044,
  "style_score": 0.4,
  "label": "This looks like it was written by a person. Our automated check didn't find the patterns we usually see in AI-generated writing.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "5322bfaf-49c4-4769-85f1-ac4cccf71190",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.6684,
  "model_score": 0.5943,
  "style_score": 0.7426,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "0bb05eb6-e988-4a5c-8d8f-f67677be9334",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.541,
  "model_score": 0.4998,
  "style_score": 0.5822,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "cc5cb4e2-f78b-4810-abd0-6829d2b22ff8",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.6058,
  "model_score": 0.6401,
  "style_score": 0.5715,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "d3427a8b-c633-4f69-a6f9-208c0c0d40e9",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.4849,
  "model_score": 0.5583,
  "style_score": 0.4116,
  "label": "We can't tell whether this was written by a person or with help from AI. A lot of people's own writing ends up here, so this is not a judgment about the writer, only a sign that our check couldn't decide.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
