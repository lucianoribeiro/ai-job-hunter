import unittest
from src.unified_jobs_dashboard import render
class RecruiterUsdFilterSmoke(unittest.TestCase):
    def test_filter_exists(self):
        page=render({'jobs': []}, [])
        self.assertIn('id="recruiter-usd"',page)
