"""Regression tests for QA freelance classification and Recruiter Monitor UI."""
import unittest
from src.recruiter_monitor import freelance_qa_facts
from src.unified_jobs_dashboard import render


class FreelancerQAMonitorTests(unittest.TestCase):
    def test_confirmed_freelance_qa(self):
        facts = freelance_qa_facts("QA Engineer - Freelance Remote", "USD 30/hour, 2 hours per day", "QA")
        self.assertEqual(facts["freelance_qa"], "yes")
        self.assertEqual(facts["part_time_evidence"], "2 hours per day")

    def test_regular_qa_is_not_freelance(self):
        self.assertEqual(freelance_qa_facts("Senior QA Engineer remote", "Full-time role", "QA")["freelance_qa"], "no")

    def test_manufacturing_not_labeled_freelance_qa(self):
        self.assertEqual(freelance_qa_facts("Manufacturing manager freelance", "", "Manufatura")["freelance_qa"], "no")

    def test_part_time_alone_does_not_confirm_freelance(self):
        data = freelance_qa_facts("QA Engineer part-time", "flexible hours", "QA")
        self.assertEqual(data["freelance_qa"], "no")
        self.assertEqual(data["part_time_evidence"], "part-time")

    def test_recruiter_html_contains_filter_and_combination_logic(self):
        html = render({"jobs": []}, [])
        self.assertNotIn('id="recruiter-freelance"', html)
        self.assertIn('Freelancer QA identificado', html)
        self.assertIn('card.hidden=!(area&&role&&city&&mode&&usd&&contract)', html)


if __name__ == "__main__":
    unittest.main()
