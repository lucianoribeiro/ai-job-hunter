import unittest
from src.dashboard import render, safe_url


class DashboardTests(unittest.TestCase):
    def test_escapes_unsafe_job_title(self):
        page = render({"abc": {"title": "<script>alert(1)</script>", "company": "Example", "url": "https://example.com/job", "score": 2, "status": "pending_review"}}, "now")
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_rejects_javascript_urls(self):
        self.assertEqual(safe_url("javascript:alert(1)"), "#")
        self.assertEqual(safe_url("https://example.com/job"), "https://example.com/job")

    def test_review_status_metrics(self):
        page = render({
            "a": {"status": "pending_review", "category": "freelance", "score": 80},
            "b": {"status": "interview", "category": "full-time/unspecified", "score": 70},
        }, "now")
        self.assertIn("Vagas registradas", page)
        self.assertIn("Freelance / contratos", page)
        self.assertIn('data-status="interview"', page)
        self.assertIn("now", page)

    def test_ignores_unknown_status(self):
        page = render({"bad": {"status": "auto_sent", "score": 50}}, "now")
        self.assertNotIn('data-status="auto_sent"', page)


if __name__ == "__main__":
    unittest.main()
