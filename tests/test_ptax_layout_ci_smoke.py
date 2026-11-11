import unittest
from src.finance_advisor import render_advisor
class PtaxLayoutSmoke(unittest.TestCase):
 def test_button(self):
  self.assertIn('fc-fx-actions',render_advisor())
