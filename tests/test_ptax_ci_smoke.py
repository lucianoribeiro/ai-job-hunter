import unittest
from src.finance_advisor import render_advisor
class PtaxSmoke(unittest.TestCase):
 def test_ptax_ui(self):
  self.assertIn('CotacaoDolarDia',render_advisor())
