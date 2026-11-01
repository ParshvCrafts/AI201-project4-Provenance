"""Unit tests for scoring.py: the combining rule and the label mapping."""

import unittest

import config
import scoring

GRID = [i / 20 for i in range(21)]  # 0.00, 0.05, ... 1.00


class CombineSignals(unittest.TestCase):

    def test_equal_weighted_average_when_signals_agree(self):
        self.assertAlmostEqual(scoring.combine_signals(0.8, 0.6), 0.7)
        self.assertAlmostEqual(scoring.combine_signals(0.2, 0.4), 0.3)

    def test_agreeing_extremes_stay_extreme(self):
        self.assertAlmostEqual(scoring.combine_signals(1.0, 1.0), 1.0)
        self.assertAlmostEqual(scoring.combine_signals(0.0, 0.0), 0.0)

    def test_output_always_between_zero_and_one(self):
        for m in GRID:
            for s in GRID:
                score = scoring.combine_signals(m, s)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)

    def test_strong_disagreement_is_held_in_unsure_band(self):
        # Without the cap, 1.0 and 0.45 average to 0.725, an AI label.
        for model, style in [(1.0, 0.45), (0.45, 1.0), (0.0, 0.55), (0.9, 0.1)]:
            with self.subTest(model=model, style=style):
                score = scoring.combine_signals(model, style)
                self.assertGreaterEqual(score, config.HUMAN_THRESHOLD)
                self.assertLessEqual(score, config.AI_THRESHOLD)
                self.assertEqual(scoring.score_to_label(score)[0], "unsure")

    def test_big_gap_on_the_same_side_is_not_capped(self):
        # 0.95 and 0.55 both say AI; the gap alone isn't disagreement.
        self.assertAlmostEqual(scoring.combine_signals(0.95, 0.55), 0.75)

    def test_small_disagreement_is_not_capped(self):
        # Opposite sides of 0.5 but only 0.3 apart: plain average.
        self.assertAlmostEqual(scoring.combine_signals(0.65, 0.35), 0.5)

    def test_signal_at_exactly_half_has_no_side(self):
        self.assertAlmostEqual(scoring.combine_signals(0.5, 1.0), 0.75)

    def test_rule_is_symmetric_in_its_inputs(self):
        for m in GRID:
            for s in GRID:
                self.assertAlmostEqual(scoring.combine_signals(m, s),
                                       scoring.combine_signals(s, m))


class ScoreToLabel(unittest.TestCase):

    def test_boundaries_belong_to_unsure(self):
        self.assertEqual(scoring.score_to_label(config.HUMAN_THRESHOLD)[0], "unsure")
        self.assertEqual(scoring.score_to_label(config.AI_THRESHOLD)[0], "unsure")
        self.assertEqual(scoring.score_to_label(config.HUMAN_THRESHOLD - 0.0001)[0], "human")
        self.assertEqual(scoring.score_to_label(config.AI_THRESHOLD + 0.0001)[0], "ai")

    def test_every_score_maps_to_one_of_three_and_all_three_appear(self):
        # Criterion 3, the code half: no gaps from 0.00 to 1.00.
        seen = set()
        for i in range(101):
            guess, label = scoring.score_to_label(i / 100)
            self.assertIn(guess, {"human", "unsure", "ai"})
            self.assertTrue(label)
            seen.add(guess)
        self.assertEqual(seen, {"human", "unsure", "ai"})


if __name__ == "__main__":
    unittest.main()
