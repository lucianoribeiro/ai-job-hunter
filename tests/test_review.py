import unittest

from src.review import assess, identity, reconcile


def sample(url="https://example.com/job?tracking=abc", title="QA Lead"):
    return {"url": url, "title": title, "company": "Sample Ltd", "source": "Test",
            "score": "85", "category": "freelance", "usd_confirmed": "False",
            "location": "Worldwide", "salary": ""}


class ReviewTests(unittest.TestCase):
    def test_url_dedup_removes_tracking_query(self):
        self.assertEqual(identity("https://example.com/job?a=1"), identity("https://example.com/job?b=2"))

    def test_first_seen_and_repeat(self):
        history, queue, fresh = reconcile([sample()], {}, {}, "2026-10-17")
        self.assertEqual(len(fresh), 1)
        history, queue, fresh = reconcile([sample()], history, queue, "2026-10-18")
        self.assertEqual(len(fresh), 0)
        self.assertEqual(next(iter(history.values()))["first_seen"], "2026-10-17")
        self.assertEqual(next(iter(history.values()))["last_seen"], "2026-10-18")

    def test_preserves_human_status(self):
        history, queue, _ = reconcile([sample()], {}, {}, "2026-10-17")
        entry = next(iter(queue.values()))
        entry["status"] = "approved"
        entry["notes"] = "Reviewed manually"
        _, queue, _ = reconcile([sample(title="QA Lead - refreshed")], history, queue, "2026-10-18")
        entry = next(iter(queue.values()))
        self.assertEqual(entry["status"], "approved")
        self.assertEqual(entry["notes"], "Reviewed manually")

    def test_assessment_does_not_invent_work_hours_or_reputation(self):
        result = assess(sample())
        self.assertEqual(result["two_hours_per_day"], "unverified")
        self.assertEqual(result["company_reputation"]["status"], "unverified")
        self.assertEqual(result["salary_currency"], "unspecified")

    def test_invalid_status_fails_closed(self):
        history, queue, _ = reconcile([sample()], {}, {}, "2026-10-17")
        next(iter(queue.values()))["status"] = "auto_applied"
        with self.assertRaises(ValueError):
            reconcile([sample()], history, queue, "2026-10-18")


if __name__ == "__main__":
    unittest.main()
