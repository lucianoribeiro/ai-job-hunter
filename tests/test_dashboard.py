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

    def test_company_filter_options_and_counts(self):
        page = render({
            "a": {"company": "Bosch", "status": "pending_review", "score": 80},
            "b": {"company": "Bosch", "status": "approved", "score": 70},
            "c": {"company": "IBM", "status": "pending_review", "score": 60},
        }, "now")
        self.assertIn('id="company"', page)
        self.assertIn('Bosch (2)', page)
        self.assertIn('IBM (1)', page)
        self.assertIn('data-company="bosch"', page)
        self.assertIn('row.dataset.company===company.value', page)

    def test_company_name_is_escaped(self):
        page = render({"a": {"company": '<img src=x onerror=alert(1)>',
                              "status": "approved", "score": 50}}, "now")
        self.assertIn('&lt;img', page)
        self.assertNotIn('<img src=x', page)

    def test_ignores_unknown_status(self):
        page = render({"bad": {"status": "auto_sent", "score": 50}}, "now")
        self.assertNotIn('data-status="auto_sent"', page)


if __name__ == "__main__":
    unittest.main()
