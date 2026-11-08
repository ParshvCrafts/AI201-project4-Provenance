"""Unit tests for stylometry.py, the style signal."""

import unittest

import stylometry as st

# Both have five sentences: below config.MIN_SENTENCES_FOR_SPREAD the spread
# isn't measured at all, so a shorter fixture couldn't test it.
EVEN_VARIED = (  # every sentence 8 words, almost no repeated words
    "Solar panels convert sunlight directly into usable electricity. "
    "Modern batteries store surplus energy for cloudy evenings. "
    "Smart inverters balance household demand against grid supply. "
    "Careful installation ensures safety, efficiency, and long lifespans. "
    "Local councils sometimes offer generous grants toward upfront costs."
)
LUMPY_REPETITIVE = (  # sentence lengths 2, 22, 3, 1, 2 and lots of repeats
    "I went. "
    "Then I went back to the shop and I went to the back of the shop "
    "and the shop was shut so I went home. "
    "Shop was shut. "
    "Shut. "
    "I went."
)
FOUR_EVEN = ". ".join(EVEN_VARIED.split(". ")[:4]) + "."  # same text, one sentence short


class Words(unittest.TestCase):

    def test_apostrophes_alone_are_not_words(self):
        self.assertEqual(st.words("' ' ''"), [])

    def test_contractions_stay_whole(self):
        self.assertEqual(st.words("Don't stop, it's fine"), ["don't", "stop", "it's", "fine"])


class SentenceLengthSpread(unittest.TestCase):

    def test_equal_lengths_have_no_spread(self):
        self.assertEqual(st.sentence_length_spread("One two three. Four five six."), 0.0)

    def test_known_value(self):
        # lengths 2 and 4: stdev 1.4142, mean 3
        self.assertAlmostEqual(st.sentence_length_spread("A b. C d e f."), 1.41421356 / 3, places=6)

    def test_fewer_than_two_sentences_is_zero_not_a_crash(self):
        for text in ("", "   ", "Just one sentence here", "One sentence."):
            with self.subTest(text=text):
                self.assertEqual(st.sentence_length_spread(text), 0.0)

    def test_punctuation_only_sentences_are_ignored(self):
        self.assertEqual(st.sentence_length_spread("One two. !!! Three four."), 0.0)


class TypeTokenRatio(unittest.TestCase):

    def test_empty_is_zero(self):
        self.assertEqual(st.type_token_ratio(""), 0.0)
        self.assertEqual(st.type_token_ratio("... !!!"), 0.0)

    def test_short_text_uses_plain_ratio(self):
        self.assertEqual(st.type_token_ratio("the the the cat"), 0.5)

    def test_all_unique_is_one(self):
        text = " ".join(f"w{i}" for i in range(200))
        self.assertEqual(st.type_token_ratio(text), 1.0)

    def test_long_text_uses_windows(self):
        # Two words alternating: every 50-word window holds 2 unique words.
        text = "red blue " * 100
        self.assertAlmostEqual(st.type_token_ratio(text), 2 / st.TTR_WINDOW)

    def test_length_does_not_drag_the_score_down(self):
        # The same 50-word pattern repeated: plain TTR would halve, MATTR doesn't.
        chunk = " ".join(f"w{i % 25}" for i in range(50))
        one = st.type_token_ratio(chunk)
        four = st.type_token_ratio(" ".join([chunk] * 4))
        self.assertAlmostEqual(one, four, places=6)


class PunctuationDensity(unittest.TestCase):

    def test_empty_is_zero(self):
        self.assertEqual(st.punctuation_density(""), 0.0)

    def test_counts_the_named_marks(self):
        # 4 words; , ; : ! are 4 marks
        self.assertEqual(st.punctuation_density("Hello, world; yes: no!"), 1.0)

    def test_full_stops_and_quotes_dont_count(self):
        self.assertEqual(st.punctuation_density('He said "yes". Then "no".'), 0.0)

    def test_hyphen_inside_a_word_is_not_a_dash(self):
        self.assertEqual(st.punctuation_density("a well-known fact"), 0.0)

    def test_dashes_and_ellipsis_count_once_each(self):
        # 6 words: one spaced hyphen, one em dash, one double hyphen, one ellipsis
        self.assertEqual(st.punctuation_density("wait - no — yes -- ok... fine go"), 4 / 6)


class StyleSignal(unittest.TestCase):

    def test_always_between_zero_and_one(self):
        for text in (EVEN_VARIED, LUMPY_REPETITIVE, "", "x", "One. Two. Three.",
                     "word " * 3000, "!!! ??? ..."):
            with self.subTest(text=text[:20]):
                score = st.style_signal(text)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)

    def test_even_sentences_and_varied_words_read_as_ai(self):
        self.assertGreater(st.style_signal(EVEN_VARIED), 0.8)

    def test_lumpy_sentences_and_repeated_words_read_as_human(self):
        self.assertLess(st.style_signal(LUMPY_REPETITIVE), 0.2)

    def test_no_words_is_neutral(self):
        self.assertEqual(st.style_signal(""), 0.5)
        self.assertEqual(st.style_signal("!!! ..."), 0.5)

    def test_single_sentence_spread_counts_as_neutral(self):
        # One sentence, all unique words: vocab part is 1.0, spread part is 0.5.
        text = "Every single word in this sentence appears exactly once"
        expected = st.config.STYLE_WEIGHT_SPREAD * 0.5 + st.config.STYLE_WEIGHT_VOCAB * 1.0
        self.assertAlmostEqual(st.style_signal(text), expected)

    def test_more_even_sentences_score_higher(self):
        # Same words, different sentence breaks: only spread changes.
        even = "aa bb cc dd. ee ff gg hh. ii jj kk ll. mm nn oo pp. qq rr ss tt."
        lumpy = "aa. bb cc dd ee ff gg hh ii jj. kk ll. mm. nn oo pp qq rr ss tt."
        self.assertGreater(st.style_signal(even), st.style_signal(lumpy))


class FewSentencesSpreadRule(unittest.TestCase):
    """Unit 8 fix: a spread from fewer than five sentences is noise, not evidence."""

    def expected_neutral(self, text):
        vocab = st._scale(st.type_token_ratio(text), st.config.VOCAB_HUMAN, st.config.VOCAB_AI)
        return st.config.STYLE_WEIGHT_SPREAD * 0.5 + st.config.STYLE_WEIGHT_VOCAB * vocab

    def test_cutoff_is_five(self):
        self.assertEqual(st.config.MIN_SENTENCES_FOR_SPREAD, 5)

    def test_four_sentences_spread_counts_as_neutral(self):
        self.assertEqual(len(st.sentences(FOUR_EVEN)), 4)
        self.assertAlmostEqual(st.style_signal(FOUR_EVEN), self.expected_neutral(FOUR_EVEN))

    def test_five_sentences_spread_is_measured(self):
        self.assertEqual(len(st.sentences(EVEN_VARIED)), 5)
        self.assertGreater(st.style_signal(EVEN_VARIED), self.expected_neutral(EVEN_VARIED))

    def test_lumpy_short_text_is_not_trusted_as_human_either(self):
        # The rule works both ways: three lumpy sentences don't earn "human".
        text = "I went. Then I went back to the shop and it was shut so I went home. Shut."
        self.assertAlmostEqual(st.style_signal(text), self.expected_neutral(text))

    def test_the_wizard_of_oz_passage_no_longer_reads_as_ai(self):
        # Criterion 1's false positive: three long sentences, spread 0.16, style
        # 0.73 before the fix. With the spread neutral it's vocabulary alone.
        import scenarios
        baum = scenarios.SCENARIOS[0]["texts"][1]
        self.assertTrue(baum.startswith("They now came upon more and more"))
        self.assertEqual(len(st.sentences(baum)), 3)
        self.assertLess(st.style_signal(baum), 0.5)


if __name__ == "__main__":
    unittest.main()
