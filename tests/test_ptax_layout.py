import unittest
from src.finance_advisor import render_advisor

class PtaxLayoutTests(unittest.TestCase):
    def test_button_and_status_are_separated(self):
        html=render_advisor()
        self.assertIn('class="fc-fx-actions"',html)
        self.assertIn('aria-describedby="fc-fx-status"',html)
        self.assertIn('id="fc-refresh-fx"',html)
        self.assertIn('#fc-fx-status{display:block',html)
        self.assertIn('min-height:44px',html)
