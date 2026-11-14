"""
Capstone instrumentation: every logged request carries the operational fields,
on the good path and the bad one.

    python -m unittest discover tests
"""

import hashlib
import unittest
from unittest import mock

import audit
import detector
from test_app import GOOD_TEXT, RouteTestCase

OPS_FIELDS = {"request_id", "route", "http_status", "input_bytes", "duration_ms", "cpu_ms"}


class InstrumentationTests(RouteTestCase):

    def last_entry(self):
        return audit.read_entries()[-1]

    def test_decision_has_ops_fields_and_stage_timings(self):
        r = self.submit()
        self.assertEqual(r.status_code, 200)
        entry = self.last_entry()
        self.assertTrue(OPS_FIELDS <= entry.keys(), OPS_FIELDS - entry.keys())
        self.assertEqual(entry["http_status"], 200)
        self.assertEqual(entry["route"], "/submit")
        for stage in ("model_ms", "style_ms", "score_ms"):
            self.assertGreaterEqual(entry[stage], 0)
        # the fingerprint is of the text itself, so the same text can be found again
        self.assertEqual(entry["input_sha256"],
                         hashlib.sha256(GOOD_TEXT.encode("utf-8")).hexdigest()[:16])
        self.assertEqual(entry["input_chars"], len(GOOD_TEXT))

    def test_response_header_matches_the_log_line(self):
        r = self.submit()
        self.assertEqual(r.headers["X-Request-ID"], self.last_entry()["request_id"])

    def test_rejection_is_timed_and_keeps_its_route_name(self):
        r = self.submit({"text": "too short", "creator_id": "w"})
        self.assertEqual(r.status_code, 400)
        entry = self.last_entry()
        self.assertTrue(OPS_FIELDS <= entry.keys())
        self.assertEqual(entry["http_status"], 400)
        self.assertEqual(entry["reason"], "text_too_short")
        self.assertEqual(entry["route"], "submit")  # the route's own name wins over the path

    def test_appeal_is_timed(self):
        content_id = self.submit().get_json()["content_id"]
        self.client.post("/appeal", json={"content_id": content_id, "reasoning": "I wrote it."})
        entry = self.last_entry()
        self.assertEqual(entry["event"], "appeal")
        self.assertTrue(OPS_FIELDS <= entry.keys())

    def test_a_crash_answers_json_500_and_leaves_a_log_line(self):
        # Before the capstone, this was Flask's HTML error page and no log entry.
        with mock.patch.object(detector, "model_signal", side_effect=RuntimeError("boom")):
            r = self.submit()
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json()["error"], "internal_error")
        entry = self.last_entry()
        self.assertEqual(entry["reason"], "internal_error")
        self.assertEqual(entry["event_detail"], "RuntimeError")
        self.assertEqual(entry["http_status"], 500)
        self.assertIn("duration_ms", entry)


if __name__ == "__main__":
    unittest.main()


class PinCoresTests(unittest.TestCase):
    """serve.py's AI201_CPU_CORES parser: ranges and single cores, comma separated."""

    def test_ranges_and_singles(self):
        import serve
        fake = mock.MagicMock()
        with mock.patch("psutil.Process", return_value=fake):
            cores = serve.pin_cores("0-3, 8")
        self.assertEqual(cores, [0, 1, 2, 3, 8])
        fake.cpu_affinity.assert_called_once_with([0, 1, 2, 3, 8])
