"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

import config

# Window size for the moving-average type-token ratio.
TTR_WINDOW = 50

# Punctuation that counts toward density: , ; : ( ) ! ? … and dashes. A dash is
# an em/en dash, a double hyphen, or a hyphen with a space on either side; a
# hyphen inside a word ("well-known") is not punctuation in this sense.
_PUNCT = re.compile(r"\.\.\.|…|--|[—–]|\s-\s|[,;:()!?]")


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.

    My version: coefficient of variation (stdev / mean) of words per sentence.
    0.0 means every sentence is the same length; higher means lumpier, which
    points toward human. Fewer than two sentences returns 0.0, and
    `style_signal` treats that case as "can't tell" instead of "AI".
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    return statistics.stdev(lengths) / statistics.mean(lengths)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.

    My version: the moving-average TTR (MATTR, Covington & McFall 2010). It
    takes the plain ratio inside every 50-word window and averages them, so a
    300-word text and a 100-word text land on the same scale. Texts shorter
    than one window fall back to the plain ratio. No words returns 0.0.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    if len(tokens) <= TTR_WINDOW:
        return len(set(tokens)) / len(tokens)
    windows = len(tokens) - TTR_WINDOW + 1
    total = sum(
        len(set(tokens[i:i + TTR_WINDOW])) / TTR_WINDOW for i in range(windows)
    )
    return total / windows


def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.

    My version: marks other than the full stop, per word. Commas, semicolons,
    colons, dashes, brackets, question marks, exclamation marks and ellipses
    count. Full stops don't (every text has them) and neither do quote marks
    or in-word hyphens (those follow the content, not the writer's habits).
    No words returns 0.0.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(_PUNCT.findall(text)) / len(tokens)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.

    My version, with the numbers in config.py:
      - spread: LOW means AI-like, so it's flipped (SPREAD_HUMAN -> 0, SPREAD_AI -> 1).
      - vocabulary: HIGH means AI-like in my calibration (the opposite of the
        hint above), so it isn't flipped (VOCAB_HUMAN -> 0, VOCAB_AI -> 1).
      - punctuation: not weighted, see config.py.
    Then 0.6 x spread + 0.4 x vocabulary. A text with fewer than two sentences
    has no spread to measure, so that part counts as 0.5 ("can't tell"), and a
    text with no words at all scores 0.5 overall.
    """
    if not words(text):
        return 0.5
    if len(sentences(text)) < 2:
        spread_part = 0.5
    else:
        spread_part = _scale(sentence_length_spread(text),
                             config.SPREAD_HUMAN, config.SPREAD_AI)
    vocab_part = _scale(type_token_ratio(text), config.VOCAB_HUMAN, config.VOCAB_AI)
    return (config.STYLE_WEIGHT_SPREAD * spread_part
            + config.STYLE_WEIGHT_VOCAB * vocab_part)


def _scale(value: float, zero_at: float, one_at: float) -> float:
    """Map `value` linearly so `zero_at` -> 0.0 and `one_at` -> 1.0, clamped."""
    return min(max((value - zero_at) / (one_at - zero_at), 0.0), 1.0)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\npunctuation_density is shown but not weighted; see config.py.")
