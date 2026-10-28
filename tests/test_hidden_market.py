import unittest
import tempfile
from pathlib import Path
from src.hidden_market import evaluate, render, discover_boards, compare_known_jobs, REMOTE


class HiddenMarketTests(unittest.TestCase):
    def setUp(self):
        self.board = {"company": "Example", "provider": "greenhouse", "slug": "example"}

    def test_engineering_signal_is_not_confirmed_opening(self):
        result = evaluate(self.board, [{"title": "Senior Software Engineer", "url": "https://example.org/job"}])
        self.assertEqual(result["signal"], "engineering_hiring_without_public_qa_listing")
        self.assertFalse(result["verified_hidden_opening"])
        self.assertEqual(result["brazil_eligibility"], "unverified")

    def test_existing_qa_opening_does_not_claim_missing_qa(self):
        result = evaluate(self.board, [
            {"title": "Software Engineer", "url": "https://example.org/eng"},
            {"title": "QA Manager", "url": "https://example.org/qa"}])
        self.assertEqual(result["qa_roles"], 1)
        self.assertEqual(result["signal"], "engineering_hiring_with_public_qa_listing")

    def test_discovers_only_public_ats_hosts_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "jobs.csv"
            path.write_text(
                "url,company\n"
                "https://jobs.lever.co/example/abc,Example\n"
                "https://jobs.lever.co/example/def,Example\n"
                "https://evil.example/jobs.lever.co/hack/one,Malicious\n", encoding="utf-8")
            boards = discover_boards({"company_boards": []}, path)
            self.assertEqual(len(boards), 1)
            self.assertEqual(boards[0]["slug"], "example")

    def test_remote_pattern_and_new_qa_titles(self):
        self.assertTrue(REMOTE.search("Remote - LATAM"))
        result = evaluate(self.board, [{"title": "Software Development Engineer in Test",
                                       "url": "https://example.org/qa",
                                       "location": "Remote Brazil"}])
        self.assertEqual(result["qa_roles"], 1)
        self.assertEqual(result["remote_engineering_roles"], 0)

    def test_new_qa_comparison_against_csv(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "jobs.csv"
            path.write_text("url,company\nhttps://example.org/known?track=1,Example\n", encoding="utf-8")
            items = [{"company": "Example", "qa_openings": [
                {"title": "QA Lead", "url": "https://example.org/known"},
                {"title": "QE Manager", "url": "https://example.org/new"}]}]
            result = compare_known_jobs(items, path)
            self.assertEqual(result["qa_already_collected"], 1)
            self.assertEqual(result["qa_not_in_baseline"], 1)

    def test_html_escapes_untrusted_titles(self):
        result = evaluate(self.board, [{"title": "<script>alert(1)</script> Software Engineer", "url": "https://example.org/job"}])
        page = render({"companies_checked": 1, "companies_failed": 0, "items": [result]})
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
