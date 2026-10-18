"""Regression checks for historical market intelligence."""
import unittest
from src.market_intelligence import classify, summarize


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
        self.assertFalse(result["seasonality_ready"])
        self.assertIsNone(result["best_month_to_search"])


if __name__ == "__main__":
    unittest.main()
