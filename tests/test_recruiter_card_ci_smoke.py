import unittest
from src.unified_jobs_dashboard import recruiter_index_date
class CardSmoke(unittest.TestCase):
 def test_brt(self):
  self.assertEqual(recruiter_index_date('2026-10-18T14:45:27+00:00')[0], '18/10/2026 às 11h45')
