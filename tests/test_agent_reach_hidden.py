import unittest
from src.agent_reach_hidden import canonical, classify, render, structured_results


class AgentReachHiddenTests(unittest.TestCase):
    def test_rejects_generic_engineering_expansion(self):
        report = classify([{"url": "https://example.org/post", "excerpt": "We're scaling engineering and hiring software developers."}])
        self.assertEqual(report["signals"], 0)

    def test_qa_intent_is_potential_not_confirmed(self):
        report = classify([{"url": "https://example.org/post?q=1", "excerpt": "We are hiring quality engineering leadership."}])
        self.assertEqual(report["signals"], 1)
        self.assertFalse(report["items"][0]["verified_hidden_opening"])
        self.assertEqual(report["not_in_baseline_by_url"], 1)

    def test_known_url_dedup_and_provenance(self):
        report = classify([
            {"url": "https://example.org/post?x=1", "excerpt": "Hiring QA lead"},
            {"url": "https://example.org/post?x=2", "excerpt": "Hiring QA lead"},
        ], {"https://example.org/post"})
        self.assertEqual(report["signals"], 1)
        self.assertEqual(report["not_in_baseline_by_url"], 0)

    def test_rejects_bad_urls_and_escapes(self):
        report = classify([{"url": "https://example.org/qa", "excerpt": "Hiring QA lead <script>alert(1)</script>"},
                           {"url": "javascript:alert(1)", "excerpt": "Hiring QA lead"}])
        output = render(report)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertEqual(canonical("http://example.org/post"), "")


    def test_structured_sources_not_neighboring_urls(self):
        data = '{"results":[{"title":"We are hiring QA Lead","url":"https://www.linkedin.com/posts/recruiter_hiring-qa-123","snippet":"We are hiring a QA Lead"},{"title":"Unrelated profile","url":"https://www.linkedin.com/in/person","snippet":"Hiring QA teams"}]}'
        parsed = structured_results(data)
        self.assertEqual(len(parsed), 2)
        result = classify(parsed)
        self.assertEqual(result["signals"], 1)
        self.assertIn("/posts/", result["items"][0]["url"])

    def test_rejects_job_board_and_search_page(self):
        report = classify([
            {"url": "https://remoteotter.com/company/test/jobs/qa-lead", "excerpt": "Hiring QA Lead"},
            {"url": "https://uk.indeed.com/q-qa-manager-jobs.html", "excerpt": "Hiring QA Manager"},
            {"url": "https://www.linkedin.com/company/test", "excerpt": "Hiring QA Lead"}
        ])
        self.assertEqual(report["signals"], 0)

    def test_fail_closed_on_unstructured_text(self):
        self.assertEqual(structured_results("text https://www.linkedin.com/in/person hiring QA"), [])

if __name__ == "__main__":
    unittest.main()
