"""
Route tests for app.py. The detector is stubbed so these run in milliseconds,
and the audit log is pointed at a temp folder so the real logs/audit.jsonl is
never touched.

    python -m unittest discover tests
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as app_module
import audit
import config
import detector

GOOD_TEXT = (
    "I walked to the corner shop this morning because we ran out of milk. "
    "The man behind the counter said the delivery truck was late again. "
    "So I bought oat milk, which nobody in my house likes, and came home."
)
DECISION_FIELDS = {
    "timestamp", "content_id", "creator_id", "guess", "model_score",
    "style_score", "combined_score", "label", "status",
}


class RouteTestCase(unittest.TestCase):
    """Fresh audit log and a stubbed model signal for every test."""

    model_score = 0.5

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        log_dir = Path(tmp.name)
        for name, value in {"LOG_DIR": log_dir, "AUDIT_LOG": log_dir / "audit.jsonl"}.items():
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        patcher = mock.patch.object(detector, "model_signal", return_value=self.model_score)
        self.model_signal = patcher.start()
        self.addCleanup(patcher.stop)

        self.client = app_module.app.test_client()

    def submit(self, body=None, **kwargs):
        if body is None:
            body = {"text": GOOD_TEXT, "creator_id": "writer_1"}
        return self.client.post("/submit", json=body, **kwargs)

    def rejections(self):
        return [e for e in audit.read_entries() if e.get("event") == "rejected"]


class SubmitHappyPath(RouteTestCase):

    def test_returns_every_contract_field(self):
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(set(body), {
            "content_id", "creator_id", "guess", "confidence", "label",
            "model_score", "style_score", "status",
        })
        self.assertIn(body["guess"], {"ai", "human", "unsure"})
        self.assertIsInstance(body["label"], str)
        self.assertTrue(body["label"])
        self.assertEqual(body["status"], "decided")
        self.assertEqual(body["model_score"], 0.5)
        for field in ("confidence", "model_score", "style_score"):
            self.assertGreaterEqual(body[field], 0.0)
            self.assertLessEqual(body[field], 1.0)

    def test_logs_one_decision_with_all_nine_fields_and_both_scores(self):
        body = self.submit().get_json()
        entries = audit.read_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertTrue(DECISION_FIELDS <= set(entry))
        self.assertEqual(entry["content_id"], body["content_id"])
        self.assertEqual(entry["creator_id"], "writer_1")
        self.assertEqual(entry["model_score"], body["model_score"])
        self.assertEqual(entry["style_score"], body["style_score"])
        self.assertEqual(entry["combined_score"], body["confidence"])
        self.assertEqual(entry["label"], body["label"])
        self.assertEqual(entry["status"], "decided")

    def test_content_ids_are_unique(self):
        first = self.submit().get_json()["content_id"]
        second = self.submit().get_json()["content_id"]
        self.assertNotEqual(first, second)

    def test_creator_id_is_trimmed(self):
        body = self.submit({"text": GOOD_TEXT, "creator_id": "  writer_1  "}).get_json()
        self.assertEqual(body["creator_id"], "writer_1")

    def test_exactly_min_words_is_accepted(self):
        text = " ".join(["word"] * config.MIN_WORDS) + "."
        self.assertEqual(self.submit({"text": text, "creator_id": "w"}).status_code, 200)

    def test_exactly_max_chars_is_accepted(self):
        text = ("Some words here. " * 2000)[:config.MAX_TEXT_CHARS]
        self.assertEqual(len(text), config.MAX_TEXT_CHARS)
        self.assertEqual(self.submit({"text": text, "creator_id": "w"}).status_code, 200)


class SubmitBadInput(RouteTestCase):
    """Criterion 5: every bad body is a 4xx JSON error and one rejected entry."""

    CASES = [
        ("empty text", {"text": "", "creator_id": "w"}, 400, "invalid_text"),
        ("only spaces", {"text": "   \n\t ", "creator_id": "w"}, 400, "invalid_text"),
        ("no text field", {"creator_id": "w"}, 400, "invalid_text"),
        ("text is null", {"text": None, "creator_id": "w"}, 400, "invalid_text"),
        ("text is a number", {"text": 42, "creator_id": "w"}, 400, "invalid_text"),
        ("text is a list", {"text": ["a", "b"], "creator_id": "w"}, 400, "invalid_text"),
        ("50,000 words", {"text": "word " * 50_000, "creator_id": "w"}, 413, "text_too_long"),
        ("one char over max", {"text": "a" * (config.MAX_TEXT_CHARS + 1), "creator_id": "w"},
         413, "text_too_long"),
        ("too few words", {"text": " ".join(["word"] * (config.MIN_WORDS - 1)), "creator_id": "w"},
         400, "text_too_short"),
        ("no creator_id", {"text": GOOD_TEXT}, 400, "invalid_creator_id"),
        ("blank creator_id", {"text": GOOD_TEXT, "creator_id": "  "}, 400, "invalid_creator_id"),
        ("creator_id is a number", {"text": GOOD_TEXT, "creator_id": 7}, 400, "invalid_creator_id"),
        ("creator_id too long", {"text": GOOD_TEXT, "creator_id": "x" * 101}, 400, "invalid_creator_id"),
        ("body is a list", ["not", "an", "object"], 400, "invalid_json"),
        ("body is a string", "just a string", 400, "invalid_json"),
    ]

    def test_each_bad_body(self):
        for name, body, status, code in self.CASES:
            with self.subTest(name):
                before = len(self.rejections())
                response = self.submit(body)
                self.assertEqual(response.status_code, status)
                payload = response.get_json()
                self.assertEqual(payload["error"], code)
                self.assertIsInstance(payload["message"], str)
                rejections = self.rejections()
                self.assertEqual(len(rejections), before + 1)
                self.assertEqual(rejections[-1]["reason"], code)
                self.assertNotIn("content_id", rejections[-1])
        self.model_signal.assert_not_called()
        self.assertFalse([e for e in audit.read_entries() if e.get("status") == "decided"])

    def test_not_json_at_all(self):
        response = self.client.post("/submit", data="text=hello", content_type="text/plain")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_json")
        self.assertEqual(len(self.rejections()), 1)

    def test_broken_json(self):
        response = self.client.post("/submit", data="{not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_json")

    def test_body_over_request_limit_is_json_413_and_logged(self):
        huge = json.dumps({"text": "a" * (config.MAX_REQUEST_BYTES + 10), "creator_id": "w"})
        response = self.client.post("/submit", data=huge, content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.get_json()["error"], "text_too_long")
        self.assertEqual(len(self.rejections()), 1)

    def test_rejection_keeps_creator_when_known(self):
        self.submit({"text": "", "creator_id": "writer_9"})
        self.assertEqual(self.rejections()[-1]["creator_id"], "writer_9")

    def test_detector_unavailable_is_503_and_logged(self):
        self.model_signal.side_effect = detector.DetectorUnavailable("no model")
        response = self.submit()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"], "detector_unavailable")
        self.assertEqual(self.rejections()[-1]["reason"], "detector_unavailable")

    def test_detector_too_short_is_400(self):
        self.model_signal.side_effect = ValueError("too short")
        response = self.submit()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "text_too_short")


if __name__ == "__main__":
    unittest.main()
