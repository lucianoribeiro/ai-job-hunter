import unittest
from src.finance_advisor import render_advisor

class PtaxAndCurrencyTests(unittest.TestCase):
 def test_ptax_source_date_and_fallback(self):
  page=render_advisor()
  self.assertIn('CotacaoDolarDia',page)
  self.assertIn('id="fc-refresh-fx"',page)
  self.assertIn('id="fc-fx-status"',page)
  self.assertIn('Cotação manual',page)
  self.assertIn('PTAX venda BCB de',page)
 def test_clt_salary_independent_of_proposal_currency(self):
  page=render_advisor()
  self.assertIn("salary=parse(el('salary').value),brl=salary",page)
  self.assertIn("el('contract').value==='B2B'?'USD':'BRL'",page)
  self.assertIn('id="fc-fx-spread"',page)
  self.assertIn("showUsd=isB2B||currency==='USD'",page)
