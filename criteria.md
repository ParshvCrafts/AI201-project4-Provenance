# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. No human writing gets the AI label

Of 10 pieces of writing I know a person wrote (my own writing plus pre-2020
published prose, including at least 3 written plainly), **0** get the
high-confidence AI label, in every one of the 3 trials.

**Why this target:** The AI label is the one that accuses somebody. The unsure
band exists so the system has somewhere to put its doubt, so known-human text
should land there at worst. On a writing site a wrong accusation costs the
writer a lot more than a missed detection costs the site, and "1 in 10" would
mean accepting that every tenth honest writer gets accused.

---

## 2. AI and human text score clearly apart

Across 5 texts I'm confident are AI-generated and 5 I'm confident are
human-written, the average `confidence` of the AI group is at least **0.40**
higher than the average of the human group, in every trial.

**Why this target:** If the two groups sit closer than that, the unsure band
(0.35 to 0.70, which is 0.35 wide) swallows both of them and the labels stop
meaning anything. My calibration run had a gap of about 0.41 to 0.65, so 0.40
is reachable but not guaranteed.

---

## 3. All three labels are reachable

A set of 6 inputs spread across the range (clearly AI, edited AI, formal human,
plain human, casual human, borderline) produces **each of the three labels at
least once** in every trial. Also, every score from 0.00 to 1.00 in steps of
0.01 maps to exactly one label (checked by a unit test).

**Why this target:** A label nobody can get is a gap in the ranges, and a
gap means some score has no sentence to show. Checking the full 0-1 sweep
catches gaps in the code; checking real inputs catches labels that exist on
paper but that my signals never actually produce.

---

## 4. Every appeal changes status and gets recorded

**10 of 10** appeals against real `content_id`s return 200 with status
`under_review`, each adds exactly one `appeal` entry to the audit log, and the
original decision entry is still there unchanged afterwards. An appeal against
a made-up id returns 404 and writes no appeal entry.

**Why this target:** The appeal is the only thing between a wrong accusation
and nothing at all, so "most of the time" isn't good enough here. And an appeal
that overwrites the original decision would destroy the evidence the reviewer
needs.

---

## 5. Bad input never crashes the service

Each of these 7 request bodies returns a **4xx JSON error, never a 500**, and
leaves exactly one `rejected` entry in the audit log: empty text,
text that is only spaces, no `text` field, `text: null`, `text` as a number, a 50,000-word
text, and no `creator_id`.

**Why this target:** A crash on malformed input is one of the most common real
failures there is, and a request that crashes leaves no trace in the log. An
attack that shows up only as an absence is one I'd never find.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
