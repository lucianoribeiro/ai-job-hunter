import unittest
from src.agent_reach_hidden import canonical, classify, render


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


if __name__ == "__main__":
    unittest.main()
