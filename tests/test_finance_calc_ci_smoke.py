import unittest
from src.finance_advisor import render_advisor
class FinanceSmoke(unittest.TestCase):
 def test_button(self):
  self.assertIn('id="fc-calculate"',render_advisor())
