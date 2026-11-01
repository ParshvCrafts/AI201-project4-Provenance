"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400


# ─── Input limits ────────────────────────────────────────────────────────────
# Anything outside these gets a 4xx and a `rejected` entry in the audit log.
#
# MIN_WORDS: below ~20 words perplexity swings wildly and there are too few
# sentences for a spread, so any label would be a guess. Saying "too short to
# check" is more honest than labelling it.
# MAX_TEXT_CHARS: about 3,500 words, longer than any single post this is for.
# The detector only reads the first 400 tokens anyway.
# MAX_REQUEST_BYTES: refuses a huge body before Flask even parses it.

MIN_WORDS = 20
MAX_TEXT_CHARS = 20_000
MAX_CREATOR_ID_CHARS = 100
MAX_REASONING_CHARS = 5_000
MAX_REQUEST_BYTES = 1_000_000


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# How much each signal counts toward the combined score.
#
# My rule (scoring.py::combine_signals, numbers in the README):
#   1. Equal-weight average. Each signal wrongly suspects a different kind of
#      human writer (model: plain writing; style: formal writing), so neither
#      earned more trust in calibration.
#   2. If the signals sit on opposite sides of 0.5 AND differ by at least
#      DISAGREEMENT_GAP, the result is held inside the unsure band. Two methods
#      that disagree that much is uncertainty, not a verdict.

WEIGHT_MODEL_SIGNAL = 0.5
WEIGHT_STYLE_SIGNAL = 0.5
DISAGREEMENT_GAP = 0.4


# ─── The style signal (stylometry.py::style_signal) ─────────────────────────
# Each measure is mapped linearly onto 0-1 (1 = AI-like) between two anchors,
# then clamped. The anchors are rounded from calibrate.py's run: AI samples had
# sentence spread 0.14-0.22 and vocabulary 0.88-0.90; human samples had spread
# 0.27-0.72 and vocabulary 0.71-0.83. Six texts is a small sample, so these are
# a starting point that unit 8 is meant to test, not a fitted model.

SPREAD_AI = 0.15       # spread at or below this scores 1.0
SPREAD_HUMAN = 0.60    # spread at or above this scores 0.0
VOCAB_HUMAN = 0.72     # moving-average TTR at or below this scores 0.0
VOCAB_AI = 0.90        # at or above this scores 1.0

# Spread separated AI from human best, so it leads. Punctuation density is
# computed and printed but not weighted: in calibration it didn't separate the
# two at all (AI 0.08-0.10, human 0.04-0.13), so it would only add noise.
STYLE_WEIGHT_SPREAD = 0.6
STYLE_WEIGHT_VOCAB = 0.4


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score < HUMAN_THRESHOLD          -> high-confidence human
#   between the two                  -> unsure
#   score > AI_THRESHOLD             -> high-confidence AI
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.

# Asymmetric on purpose. A wrong "AI" label accuses a writer; a wrong "human"
# label lets some AI text through. So the AI label needs 0.70, which leaves
# formal human writing (0.56 in calibration) real headroom, while edited AI
# (0.76) is still caught. Both boundaries belong to "unsure".

HUMAN_THRESHOLD = 0.35
AI_THRESHOLD = 0.70

# ⚠️ One thing that catches people out in Milestone 5. A weighted average can
# only land between its two inputs — so while `style_signal` is still the stub
# returning 0.5, the combined score can never leave 0.25–0.75 no matter what
# the model signal says, and the human label needs a model score below 0.20 to
# be reachable at all.
#
# If a label you can't reach is the problem, the fix is upstream of the
# thresholds: a style signal that actually varies. `scoring.label_ranges()`
# prints the bands; the reachable range is a different question.


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# Off in unit 7. You turn it on and choose the numbers in unit 8, Milestone 1.
#
# Think about two people: a real writer submitting their own work a few times
# an hour, and a script sending a thousand variations to map your thresholds.
# Your README has to say why your numbers and not others.

RATE_LIMITING_ENABLED = os.getenv("AI201_RATE_LIMITS", "0") == "1"

RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_DAY = 200

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
