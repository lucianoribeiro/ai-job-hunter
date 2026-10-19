import unittest
from src.recruiter_monitor import advertised_usd_salary, QA_SEARCHES

class RecruiterUsdTests(unittest.TestCase):
    def test_hourly_range(self):
        self.assertEqual(advertised_usd_salary('US$ 63 a US$ 120 por hora'), 'US$ 63–120 /hora')
    def test_monthly_and_missing(self):
        self.assertEqual(advertised_usd_salary('USD 6500 per month'), 'US$ 6500 /mês')
        self.assertIsNone(advertised_usd_salary('Excellent compensation'))
    def test_qa_queries(self):
        self.assertGreaterEqual(len(QA_SEARCHES), 5)

    def test_usd_only_filter_is_present_and_composable(self):
        from src.unified_jobs_dashboard import render
        page = render({'jobs': []}, [])
        self.assertIn('id="recruiter-usd"', page)
        self.assertIn('Somente vagas com salário em USD', page)
        self.assertIn('card.dataset.usd===recruiterUsd.value', page)
        self.assertIn('area&&role&&city&&mode&&usd&&contract', page)
        self.assertIn('id="recruiter-clear"', page)
