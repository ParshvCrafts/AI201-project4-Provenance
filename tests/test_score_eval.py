"""
Tests for score_eval.py: the pass/fail rule for each of my five criteria.

    python -m unittest discover tests
"""

import unittest

import score_eval as se


def decided(guess, confidence=0.5, status=200):
    return {"status": status, "guess": guess, "confidence": confidence, "log_delta": 1}


def appealed(**overrides):
    result = {"status": 200, "guess": "unsure", "confidence": 0.5, "log_delta": 1,
              "appeal_status": 200, "appeal_body_status": "under_review",
              "status_after": "under_review", "appeal_entries": 1,
              "original_decision_intact": True}
    result.update(overrides)
    return result


FAKE_OK = {"sent": "appeal against a made-up content_id", "appeal_status": 404,
           "appeal_entries": 0}


class Criterion1HumanNeverLabelledAI(unittest.TestCase):
    def test_no_ai_labels_passes(self):
        ok, cell = se.criterion_1([decided("unsure")] * 9 + [decided("human")])
        self.assertTrue(ok)
        self.assertEqual(cell, "0/10")

    def test_one_ai_label_fails(self):
        ok, cell = se.criterion_1([decided("unsure")] * 9 + [decided("ai")])
        self.assertFalse(ok)
        self.assertEqual(cell, "1/10")

    def test_a_crash_is_not_a_pass(self):
        # A text that never got a label wasn't shown to be safe.
        ok, cell = se.criterion_1([decided("unsure")] * 9 + [{"status": None, "error": "x"}])
        self.assertFalse(ok)
        self.assertIn("1 not scored", cell)


class Criterion2ScoreSpread(unittest.TestCase):
    def results(self, ai, human):
        return [decided("ai", c) for c in ai] + [decided("human", c) for c in human]

    def test_gap_of_exactly_040_passes(self):
        ok, cell = se.criterion_2(self.results([0.8] * 5, [0.4] * 5))
        self.assertTrue(ok)
        self.assertEqual(cell, "gap 0.40")

    def test_gap_under_040_fails(self):
        ok, _ = se.criterion_2(self.results([0.7] * 5, [0.31] * 5))
        self.assertFalse(ok)

    def test_missing_confidence_fails(self):
        results = self.results([0.9] * 5, [0.1] * 5)
        results[2] = {"status": 500, "confidence": None}
        ok, cell = se.criterion_2(results)
        self.assertFalse(ok)
        self.assertIn("not scored", cell)


class Criterion3LabelCoverage(unittest.TestCase):
    def test_all_three_passes(self):
        ok, cell = se.criterion_3([decided("ai"), decided("unsure"), decided("human")])
        self.assertTrue(ok)
        self.assertEqual(cell, "3/3")

    def test_missing_human_fails_and_says_which(self):
        ok, cell = se.criterion_3([decided("ai"), decided("unsure"), decided("unsure")])
        self.assertFalse(ok)
        self.assertEqual(cell, "2/3 (no human)")


class Criterion4Appeals(unittest.TestCase):
    def test_ten_good_appeals_and_a_404_passes(self):
        ok, cell = se.criterion_4([appealed()] * 10 + [FAKE_OK])
        self.assertTrue(ok)
        self.assertEqual(cell, "10/10, fake id 404")

    def test_overwritten_decision_fails(self):
        results = [appealed()] * 9 + [appealed(original_decision_intact=False)] + [FAKE_OK]
        ok, cell = se.criterion_4(results)
        self.assertFalse(ok)
        self.assertTrue(cell.startswith("9/10"))

    def test_two_appeal_entries_fails(self):
        ok, _ = se.criterion_4([appealed(appeal_entries=2)] + [appealed()] * 9 + [FAKE_OK])
        self.assertFalse(ok)

    def test_submission_that_never_got_appealed_fails(self):
        ok, _ = se.criterion_4([decided("unsure", status=429)] + [appealed()] * 9 + [FAKE_OK])
        self.assertFalse(ok)

    def test_fake_id_that_writes_an_appeal_fails(self):
        ok, cell = se.criterion_4([appealed()] * 10 + [dict(FAKE_OK, appeal_entries=1)])
        self.assertFalse(ok)
        self.assertIn("fake id FAILED", cell)

    def test_no_fake_appeal_sent_fails(self):
        ok, _ = se.criterion_4([appealed()] * 10)
        self.assertFalse(ok)


class Criterion5BadInput(unittest.TestCase):
    def rejected(self, status=400, delta=1, error="invalid_text"):
        return {"status": status, "error": error, "log_delta": delta}

    def test_seven_clean_rejections_pass(self):
        ok, cell = se.criterion_5([self.rejected()] * 6 + [self.rejected(413, error="text_too_long")])
        self.assertTrue(ok)
        self.assertEqual(cell, "7/7")

    def test_a_500_fails(self):
        ok, cell = se.criterion_5([self.rejected()] * 6 + [self.rejected(500)])
        self.assertFalse(ok)
        self.assertEqual(cell, "6/7")

    def test_unlogged_rejection_fails(self):
        ok, _ = se.criterion_5([self.rejected()] * 6 + [self.rejected(delta=0)])
        self.assertFalse(ok)

    def test_non_json_error_fails(self):
        ok, _ = se.criterion_5([self.rejected()] * 6 + [self.rejected(error=None)])
        self.assertFalse(ok)


class Verdict(unittest.TestCase):
    def test_must_hold_in_every_trial(self):
        self.assertEqual(se.verdict([True, True, False]), "MISSED")
        self.assertEqual(se.verdict([True, True, True]), "MET")

    def test_no_trials_is_not_a_pass(self):
        self.assertEqual(se.verdict([]), "MISSED")

    def test_table_has_one_row_per_criterion(self):
        run = [{"criterion": 3, "name": "label coverage",
                "trials": [[decided("ai"), decided("unsure"), decided("human")]] * 3}]
        rows = se.table(run)
        self.assertEqual(len(rows), 1)
        self.assertIn("| 3/3 | 3/3 | 3/3 | MET |", rows[0])


if __name__ == "__main__":
    unittest.main()
