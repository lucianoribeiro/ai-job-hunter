import unittest
from src.linkedin_history import retain
from src.market_intelligence import summarize

class LinkedInHistoryTests(unittest.TestCase):
    def test_deduplicates_and_ignores_unrelated_posts(self):
        feed = {"date_utc": "2026-10-18", "items": [
            {"title": "QA Manager hiring", "url": "https://example.com/1", "published_at": "2026-10-18T10:00:00+00:00", "area": "QA"},
            {"title": "Other", "url": "https://example.com/2", "published_at": "2026-10-18T10:00:00+00:00", "area": "Outros"}]}
        first = retain({}, feed)
        self.assertEqual(len(first), 1)
        self.assertEqual(retain(first, feed), first)

    def test_linkedin_monthly_is_separate_from_job_history(self):
        posts = retain({}, {"date_utc": "2026-10-18", "items": [
            {"title": "QA Manager hiring", "url": "https://example.com/1", "published_at": "2026-10-18T10:00:00+00:00", "area": "QA"}]})
        report = summarize({}, "2026-10-18", posts)
        self.assertEqual(report["linkedin"]["categories"]["QA"]["monthly"][-1], 1)
        self.assertIsNone(report["linkedin"]["categories"]["QA"]["monthly"][-2])
        self.assertEqual(report["categories"]["QA"]["monthly"][-1], 0)

if __name__ == "__main__":
    unittest.main()
