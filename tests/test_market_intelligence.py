"""Regression checks for historical market intelligence."""
import unittest
from unittest.mock import patch
from src.market_intelligence import classify, summarize
from src.unified_jobs_dashboard import market_chart_html


class MarketIntelligenceTests(unittest.TestCase):
    def test_classification_separates_technology_and_manufacturing(self):
        self.assertEqual(classify("QA Manager"), "QA Manager")
        self.assertEqual(classify("Senior QA Engineer"), "QA")
        self.assertEqual(classify("Manufacturing Project Manager"), "Manufatura")
        self.assertIsNone(classify("IT Project Manager"))

    def test_history_is_deduplicated_and_no_seasonality_inferred(self):
        history = {
            "id-1": {"title": "QA Manager", "first_seen": "2026-09-03", "company": "A", "source": "Source A"},
            "id-2": {"title": "QA Manager", "first_seen": "2026-09-04", "company": "A", "source": "Source A"},
            "id-3": {"title": "Manufacturing Coordinator", "first_seen": "2026-10-01", "company": "B", "source": "Source B"},
        }
        result = summarize(history, "2026-10-18")
        self.assertEqual(result["categories"]["QA Manager"]["monthly"][-2], 2)
        self.assertEqual(result["categories"]["Manufatura"]["monthly"][-1], 1)
        self.assertEqual(len(result["months"]), 24)
        self.assertEqual(result["months"][0], "11/2024")
        self.assertEqual(result["months"][-1], "10/2026")
        self.assertFalse(result["seasonality_ready"])
        self.assertIsNone(result["best_month_to_search"])

    def test_dashboard_separates_vacancies_from_recruiter_posts(self):
        report = summarize({}, "2026-10-18", {
            "post-1": {"area": "QA", "published_at": "2026-10-18T10:00:00+00:00"}
        })
        with patch("src.market_intelligence.summarize", return_value=report):
            chart = market_chart_html(31)
        self.assertIn('id="market-recruiter-current"', chart)
        self.assertIn('id="market-metric"', chart)
        self.assertIn('<option value="posts" selected>Posts públicos indexados</option>', chart)
        self.assertIn('id="market-scope"', chart)
        self.assertIn("não são vagas verificadas", chart)
        self.assertIn('<option value="24" selected>24 meses</option>', chart)
        self.assertIn('"linkedin":', chart)
        self.assertIn('"recruiter_current": 31', chart)

    def test_linkedin_month_without_successful_query_is_not_zero(self):
        result = summarize({}, "2026-10-18", {
            "_coverage": {"2026-09": {"QA": "ok", "Manufatura": "error:TimeoutError"}}
        })
        self.assertEqual(result["linkedin"]["categories"]["QA"]["monthly"][-2], 0)
        self.assertIsNone(result["linkedin"]["categories"]["Manufatura"]["monthly"][-2])


if __name__ == "__main__":
    unittest.main()
