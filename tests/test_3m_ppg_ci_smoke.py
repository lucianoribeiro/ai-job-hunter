import unittest
from src.strategic_companies import ppg_public_jobs
class IntegrationSmoke(unittest.TestCase):
 def test_empty(self):
  self.assertEqual(ppg_public_jobs('', 'https://careers.ppg.com/br/pt/', 'PPG'), [])
