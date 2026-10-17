import unittest
from src.opportunity_assessment import assess_opportunity
from src.cv_match import compare

class EvidenceTests(unittest.TestCase):
    def test_missing_usd_and_brazil_are_unverified(self):
        result = assess_opportunity({"title": "QA Manager", "location": "USA only", "salary": ""})
        self.assertTrue(any("USD" in x for x in result["warnings"]))
        self.assertEqual(result["brazil_eligibility"], "needs_review")
        self.assertEqual(result["company_quality"], "unverified")

    def test_freelance_hours_never_inferred(self):
        result = assess_opportunity({"title": "QA Engineer", "category": "freelance"})
        self.assertTrue(any("2h/dia" in x for x in result["warnings"]))

    def test_skill_match_only_if_both_cv_and_job_contain_skill(self):
        result = assess_opportunity({"title": "QA Automation Playwright", "description": ""}, "Used Playwright for 4 years")
        self.assertIn("playwright", result["skills_matched"])

    def test_compare_returns_no_cv_contents(self):
        result = compare("My private number 111-222-333 and Selenium", [{"title": "QA Selenium", "company": "Acme"}])
        self.assertNotIn("111-222-333", str(result))
