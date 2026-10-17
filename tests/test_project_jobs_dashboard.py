import unittest
from src.project_jobs_dashboard import render


class ProjectDashboardTests(unittest.TestCase):
    def test_html_escapes_untrusted_postings(self):
        page = render({"generated_at": "test", "boards": {"ashby:test": {"fetched": 1, "matched": 1}},
            "errors": [], "jobs": [{"title": "<script>alert(1)</script>", "company": "Acme",
            "url": "javascript:alert(1)", "location": "Remote", "source": "Ashby",
            "remote_evidence": "explicit"}]})
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("href='#'", page)

    def test_empty_report_renders(self):
        page = render({"jobs": [], "boards": {}, "errors": []})
        self.assertIn("Nenhuma vaga encontrada", page)


if __name__ == "__main__":
    unittest.main()
