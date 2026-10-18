import unittest
from src.finance_advisor import render_advisor

class FinanceTaxAssumptionsTests(unittest.TestCase):
    def test_optional_tax_inputs_and_manual_calculate(self):
        page=render_advisor()
        for field in ('fc-activity','fc-rbt','fc-payroll','fc-prolabore','fc-personal-tax','fc-iss','fc-calculate'):
            self.assertIn('id="'+field+'"',page)
        self.assertIn("bracket[2]",page)
        self.assertIn("factor>=.28",page)
        self.assertIn("el('calculate').addEventListener('click',update)",page)
        self.assertIn('não apura adicional de IRPJ',page)
