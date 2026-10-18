import unittest
from src.job_history import retain
class HistoryCiSmoke(unittest.TestCase):
 def test_empty(self):
  self.assertEqual(retain({}, [], '2026-10-18'), {})
