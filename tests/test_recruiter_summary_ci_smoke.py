import unittest
from src.unified_jobs_dashboard import recruiter_index_date
class SummarySmoke(unittest.TestCase):
 def test_date(self):
  self.assertEqual(recruiter_index_date('2026-10-18T14:45:00+00:00')[0],'18/10/2026 às 11h45')
