import unittest
from src.finance_advisor import render_advisor

class FinanceCalculatorUXTests(unittest.TestCase):
    def test_salary_only_required_and_explicit_calculation(self):
        html = render_advisor()
        for field in ('fc-salary','fc-calculate','fc-results','fc-pj-regime','fc-coop-fee','fc-coop-tax'):
            self.assertIn('id="'+field+'"',html)
        self.assertIn("el('calculate').addEventListener('click',update)",html)
        self.assertNotIn("update();\n})();",html)
        self.assertIn('Cooperativa',html)
        self.assertIn('Lucro Presumido',html)
        self.assertIn('Simples Nacional',html)

    def test_contract_cards_explain_gross_targets(self):
        html=render_advisor()
        for phrase in ('Quanto pedir como PJ nacional', 'Quanto pedir em B2B internacional', 'Quanto pedir via cooperativa', 'não é salário líquido'):
            self.assertIn(phrase, html)
