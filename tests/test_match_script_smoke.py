import unittest
from src.unified_jobs_dashboard import render

class MatchScriptSmokeTests(unittest.TestCase):
    def test_buttons_exist_in_rendered_page(self):
        page=render({'jobs': []}, [])
        self.assertIn('id="matchAnalyze"',page)
        self.assertIn('id="matchFile"',page)
