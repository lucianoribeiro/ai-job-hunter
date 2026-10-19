import unittest
from src.unified_jobs_dashboard import render
class Smoke(unittest.TestCase):
 def test_render(self):
  self.assertIn('Recruiter Monitor',render({'jobs':[]},[]))
