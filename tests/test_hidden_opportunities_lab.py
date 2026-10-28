import unittest
from src.hidden_opportunities_lab import investigate, report_html


class HiddenOpportunityLabTests(unittest.TestCase):
    def test_does_not_claim_any_hidden_vacancy(self):
        result = investigate([{"url":"https://www.linkedin.com/posts/company-hiring-qa",
                               "excerpt":"We're hiring a Quality Engineering Lead to expand our quality practice.",
                               "company":"Example"}])
        self.assertEqual(result["accepted_signals"], 1)
        self.assertEqual(result["confirmed_hidden_vacancies"], 0)
        self.assertEqual(result["items"][0]["status"], "potential_unconfirmed")

    def test_exclude_job_boards_profiles_and_applicants(self):
        rows = [
            {"url":"https://www.linkedin.com/in/person", "excerpt":"We are hiring QA Manager"},
            {"url":"https://jobs.lever.co/org/a", "excerpt":"We are hiring QA Manager"},
            {"url":"https://www.linkedin.com/posts/candidate", "excerpt":"Open to new opportunities, hiring QA Manager"},
            {"url":"https://example.org/article", "excerpt":"Engineering expansion with no QA mentioned"}]
        self.assertEqual(investigate(rows)["accepted_signals"], 0)

    def test_dedup_and_html_escape(self):
        rows = [{"url":"https://www.linkedin.com/posts/example?x=1",
                 "excerpt":"Hiring QA lead <script>alert(1)</script>"},
                {"url":"https://www.linkedin.com/posts/example?x=2",
                 "excerpt":"Hiring QA lead"}]
        result = investigate(rows)
        self.assertEqual(result["accepted_signals"], 1)
        page = report_html(result)
        self.assertNotIn("<script>",page)
        self.assertIn("&lt;script&gt;",page)


if __name__ == "__main__":
    unittest.main()
