import unittest
from src.ai_advisor import summarize
from src.dashboard import render

class AdvisorTests(unittest.TestCase):
    def test_summary_top_three(self):
        q = {str(i): {"title": "QA " + str(i), "company": "Employer", "score": i, "status": "pending_review", "assessment": {}} for i in range(5)}
        result = summarize(q)
        self.assertEqual([x["title"] for x in result["recommendations"]], ["QA 4", "QA 3", "QA 2"])
        self.assertEqual(result["mode"], "rules")

    def test_discard_dismissed(self):
        result = summarize({"a": {"title": "QA Lead", "score": 100, "status": "dismissed"}})
        self.assertEqual(result["recommendations"], [])

    def test_panel_at_top_escaped(self):
        html = render({}, insights={"headline": "<script>alert(1)</script>", "summary": "Review",
                                    "recommendations": [], "mode": "rules"})
        self.assertIn("&lt;script&gt;", html)
        self.assertLess(html.index("AI Job Hunter · Assistente"), html.index('class="stats"'))

if __name__ == "__main__":
    unittest.main()
