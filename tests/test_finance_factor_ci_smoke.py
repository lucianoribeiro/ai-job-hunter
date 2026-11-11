import unittest
from src.finance_advisor import render_advisor
class FinanceFactorSmoke(unittest.TestCase):
 def test_controls(self):
  self.assertIn('id="fc-rbt"',render_advisor())
