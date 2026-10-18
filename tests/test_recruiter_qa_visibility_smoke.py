import unittest
from src.unified_jobs_dashboard import render
class RecruiterVisibilitySmoke(unittest.TestCase):
 def test_hidden_style(self):
  self.assertIn('.recruiter-card[hidden]{display:none!important}',render({'jobs':[]},[]))
